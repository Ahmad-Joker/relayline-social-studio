from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError

from app.core.encryption import TokenCipher
from app.core.enums import Platform, SocialPostStatus
from app.db.models import SocialPost
from app.integrations.fake_social_client import ClientPublishResult, RateLimitError, RetryablePublishError
from app.services.credential_service import CredentialService
from app.services.publishing_service import PublishingService
from tests.helpers import make_campaign


class RecordingPublisher:
    def __init__(self, platform: str, outcomes=None):
        self.platform = platform
        self.outcomes = list(outcomes or [])
        self.keys: list[str] = []

    def validate_credentials(self, access_token: str) -> bool:
        return bool(access_token)

    def parse_delivery_event(self, payload: dict) -> dict:
        return payload

    def publish(self, request):
        self.keys.append(request.idempotency_key)
        if self.outcomes:
            outcome = self.outcomes.pop(0)
            if isinstance(outcome, Exception):
                raise outcome
        return ClientPublishResult(external_post_id=f"external-{self.platform}")


def build_service(session, settings, publishers):
    credentials = CredentialService(TokenCipher(settings.token_encryption_key))
    for platform in publishers:
        credentials.upsert(
            session,
            platform=Platform(platform),
            external_account_id=f"account-{platform}",
            display_name="Demo",
            token=f"token-{platform}",
        )
    return PublishingService(settings, credentials, publishers)


def test_duplicate_publish_claim_is_safe(session, settings, tmp_path):
    campaign = make_campaign(session, settings, tmp_path, (Platform.INSTAGRAM,))
    publisher = RecordingPublisher("instagram")
    service = build_service(session, settings, {"instagram": publisher})

    post_id = service.claim_due(session)
    service.process_claimed(session, post_id)
    assert service.claim_due(session) is None
    post = session.get(SocialPost, post_id)
    assert post.status == SocialPostStatus.AWAITING_DELIVERY.value
    assert publisher.keys == [post.idempotency_key]
    assert campaign.social_posts[0].id == post.id


def test_timeout_retry_reuses_stable_key_without_duplicate_logical_row(session, settings, tmp_path):
    make_campaign(session, settings, tmp_path, (Platform.X,))
    publisher = RecordingPublisher("x", [RetryablePublishError("timeout after accept")])
    service = build_service(session, settings, {"x": publisher})

    first_id = service.claim_due(session)
    service.process_claimed(session, first_id)
    post = session.get(SocialPost, first_id)
    assert post.status == SocialPostStatus.RETRY_SCHEDULED.value

    retry_id = service.claim_due(session, datetime.now(timezone.utc) + timedelta(minutes=1))
    service.process_claimed(session, retry_id)
    session.refresh(post)
    assert retry_id == first_id
    assert publisher.keys == [post.idempotency_key, post.idempotency_key]
    assert session.query(SocialPost).count() == 1
    assert post.status == SocialPostStatus.AWAITING_DELIVERY.value


def test_rate_limit_reschedules_without_hammering_then_succeeds(session, settings, tmp_path):
    make_campaign(session, settings, tmp_path, (Platform.X,))
    publisher = RecordingPublisher("x", [RateLimitError(30)])
    service = build_service(session, settings, {"x": publisher})
    post_id = service.claim_due(session)
    service.process_claimed(session, post_id)
    post = session.get(SocialPost, post_id)
    retry_at = post.next_attempt_at.replace(tzinfo=timezone.utc) if post.next_attempt_at.tzinfo is None else post.next_attempt_at

    assert post.status == SocialPostStatus.RETRY_SCHEDULED.value
    assert 25 <= (retry_at - datetime.now(timezone.utc)).total_seconds() <= 31
    assert service.claim_due(session) is None
    assert len(publisher.keys) == 1

    claimed = service.claim_due(session, datetime.now(timezone.utc) + timedelta(seconds=31))
    service.process_claimed(session, claimed)
    assert publisher.keys[0] == publisher.keys[1]
    assert session.get(SocialPost, post_id).status == SocialPostStatus.AWAITING_DELIVERY.value


def test_expired_lease_recovers_remaining_platform_without_republishing_first(session, settings, tmp_path):
    campaign = make_campaign(session, settings, tmp_path)
    instagram = RecordingPublisher("instagram")
    x_publisher = RecordingPublisher("x")
    service = build_service(session, settings, {"instagram": instagram, "x": x_publisher})

    first = service.claim_due(session)
    service.process_claimed(session, first)
    second = service.claim_due(session)
    leased = session.get(SocialPost, second)
    leased.lease_until = datetime.now(timezone.utc) - timedelta(seconds=1)
    session.commit()

    recovered = service.claim_due(session)
    service.process_claimed(session, recovered)
    assert recovered == second
    assert len(instagram.keys) + len(x_publisher.keys) == 2
    assert all(p.status == SocialPostStatus.AWAITING_DELIVERY.value for p in campaign.social_posts)


def test_database_uniqueness_blocks_duplicate_campaign_platform(session, settings, tmp_path):
    campaign = make_campaign(session, settings, tmp_path, (Platform.X,))
    original = campaign.social_posts[0]
    session.add(
        SocialPost(
            campaign_id=campaign.id,
            platform=Platform.X.value,
            caption="duplicate",
            image_path=original.image_path,
            scheduled_at=original.scheduled_at,
            next_attempt_at=original.next_attempt_at,
            status=SocialPostStatus.QUEUED.value,
            idempotency_key="different-key",
        )
    )
    try:
        session.commit()
        raise AssertionError("duplicate row unexpectedly committed")
    except IntegrityError:
        session.rollback()

