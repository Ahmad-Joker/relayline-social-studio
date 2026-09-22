import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import Settings
from app.core.enums import AttemptOutcome, CampaignStatus, SocialPostStatus
from app.db.models import Campaign, PublishAttempt, SocialPost
from app.integrations.fake_social_client import PermanentPublishError, RateLimitError, RetryablePublishError
from app.publishing.base import PublishRequest, SocialPublisher
from app.services.credential_service import CredentialService

logger = logging.getLogger(__name__)


def _aware(value: datetime | None) -> datetime | None:
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def recompute_campaign_status(session: Session, campaign_id: str) -> None:
    campaign = session.get(Campaign, campaign_id)
    if not campaign:
        return
    statuses = {post.status for post in campaign.social_posts}
    if statuses == {SocialPostStatus.PUBLISHED.value}:
        campaign.status = CampaignStatus.PUBLISHED.value
    elif SocialPostStatus.PUBLISHED.value in statuses:
        campaign.status = CampaignStatus.PARTIALLY_PUBLISHED.value
    elif statuses and statuses <= {SocialPostStatus.FAILED.value}:
        campaign.status = CampaignStatus.FAILED.value
    elif statuses & {SocialPostStatus.PUBLISHING.value, SocialPostStatus.AWAITING_DELIVERY.value, SocialPostStatus.RETRY_SCHEDULED.value}:
        campaign.status = CampaignStatus.PUBLISHING.value
    else:
        campaign.status = CampaignStatus.QUEUED.value


class PublishingService:
    def __init__(
        self,
        settings: Settings,
        credentials: CredentialService,
        publishers: dict[str, SocialPublisher],
    ):
        self.settings = settings
        self.credentials = credentials
        self.publishers = publishers

    def claim_due(self, session: Session, now: datetime | None = None) -> str | None:
        now = now or datetime.now(timezone.utc)
        due = and_(
            SocialPost.status.in_([SocialPostStatus.QUEUED.value, SocialPostStatus.RETRY_SCHEDULED.value]),
            SocialPost.next_attempt_at <= now,
        )
        abandoned = and_(
            SocialPost.status == SocialPostStatus.PUBLISHING.value,
            SocialPost.lease_until.is_not(None),
            SocialPost.lease_until <= now,
        )
        query = (
            select(SocialPost)
            .where(or_(due, abandoned))
            .order_by(SocialPost.next_attempt_at, SocialPost.id)
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        post = session.scalar(query)
        if not post:
            session.rollback()
            return None
        post.status = SocialPostStatus.PUBLISHING.value
        post.lease_until = now + timedelta(seconds=self.settings.publish_lease_seconds)
        post.publish_attempt_count += 1
        recompute_campaign_status(session, post.campaign_id)
        session.commit()
        return post.id

    def process_claimed(self, session: Session, post_id: str) -> None:
        query = select(SocialPost).where(SocialPost.id == post_id).options(selectinload(SocialPost.campaign))
        post = session.scalar(query)
        if not post or post.status != SocialPostStatus.PUBLISHING.value:
            return
        publisher = self.publishers.get(post.platform)
        if not publisher:
            self._permanent_failure(session, post, "Unsupported publishing platform")
            return
        try:
            access_token = self.credentials.token_for(session, post.platform)
            request = PublishRequest(
                social_post_id=post.id,
                caption=post.caption,
                image_bytes=Path(post.image_path).read_bytes(),
                idempotency_key=post.idempotency_key,
                access_token=access_token,
            )
            result = publisher.publish(request)
        except RateLimitError as exc:
            self._retry(session, post, exc.retry_after_seconds, AttemptOutcome.RATE_LIMITED, "Rate limited — retry scheduled")
            return
        except RetryablePublishError:
            delay = min(2 ** post.publish_attempt_count, self.settings.retry_max_seconds)
            self._retry(session, post, delay, AttemptOutcome.RETRYABLE_ERROR, "Temporary publish failure — retry scheduled")
            return
        except (PermanentPublishError, LookupError, OSError) as exc:
            safe = str(exc) if isinstance(exc, LookupError) else "Publish request cannot be completed"
            self._permanent_failure(session, post, safe)
            return
        post.external_post_id = result.external_post_id
        post.status = SocialPostStatus.AWAITING_DELIVERY.value
        post.last_error_safe = None
        post.lease_until = None
        self._record(session, post, AttemptOutcome.ACKNOWLEDGED, "Awaiting signed delivery confirmation")
        recompute_campaign_status(session, post.campaign_id)
        session.commit()
        logger.info("publish_acknowledged", extra={"campaign_id": post.campaign_id, "social_post_id": post.id, "platform": post.platform, "attempt": post.publish_attempt_count})

    def _retry(self, session: Session, post: SocialPost, seconds: int, outcome: AttemptOutcome, detail: str) -> None:
        if post.publish_attempt_count >= self.settings.max_publish_attempts:
            self._permanent_failure(session, post, "Maximum publish attempts reached")
            return
        post.status = SocialPostStatus.RETRY_SCHEDULED.value
        post.next_attempt_at = datetime.now(timezone.utc) + timedelta(seconds=seconds)
        post.lease_until = None
        post.last_error_safe = detail
        self._record(session, post, outcome, detail)
        recompute_campaign_status(session, post.campaign_id)
        session.commit()
        logger.warning("publish_retry_scheduled", extra={"campaign_id": post.campaign_id, "social_post_id": post.id, "platform": post.platform, "attempt": post.publish_attempt_count})

    def _permanent_failure(self, session: Session, post: SocialPost, detail: str) -> None:
        post.status = SocialPostStatus.FAILED.value
        post.lease_until = None
        post.last_error_safe = detail[:500]
        self._record(session, post, AttemptOutcome.PERMANENT_ERROR, post.last_error_safe)
        recompute_campaign_status(session, post.campaign_id)
        session.commit()

    @staticmethod
    def _record(session: Session, post: SocialPost, outcome: AttemptOutcome, detail: str) -> None:
        session.add(PublishAttempt(social_post_id=post.id, attempt_number=post.publish_attempt_count, outcome=outcome.value, safe_detail=detail))

