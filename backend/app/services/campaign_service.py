import hashlib
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.captions.composer import CaptionComposer
from app.core.config import Settings
from app.core.enums import CampaignStatus, Platform, SocialPostStatus
from app.db.models import BlogPost, Campaign, SocialPost, uuid_str
from app.schemas.campaign import CampaignCreate, CampaignRead, SocialPostRead
from app.services.image_service import ImageService


def stable_idempotency_key(campaign_id: str, platform: Platform) -> str:
    return hashlib.sha256(f"relayline:{campaign_id}:{platform.value}".encode()).hexdigest()


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class CampaignService:
    def __init__(self, settings: Settings, image_service: ImageService | None = None, captions: CaptionComposer | None = None):
        self.settings = settings
        self.images = image_service or ImageService()
        self.captions = captions or CaptionComposer()

    def create(self, session: Session, data: CampaignCreate) -> Campaign:
        blog = session.get(BlogPost, data.blog_post_id)
        if not blog:
            raise LookupError("Blog post not found")
        campaign_id = uuid_str()
        variants = self.images.create_variants(Path(blog.source_image_path), self.settings.generated_dir / campaign_id)
        campaign = Campaign(
            id=campaign_id,
            blog_post_id=blog.id,
            scheduled_at=data.scheduled_at.astimezone(timezone.utc),
            status=CampaignStatus.QUEUED.value,
        )
        session.add(campaign)
        for platform in data.platforms:
            session.add(
                SocialPost(
                    campaign=campaign,
                    platform=platform.value,
                    caption=self.captions.compose(platform, title=blog.title, body=blog.body, url=blog.url),
                    image_path=str(variants[platform]),
                    scheduled_at=campaign.scheduled_at,
                    next_attempt_at=campaign.scheduled_at,
                    status=SocialPostStatus.QUEUED.value,
                    idempotency_key=stable_idempotency_key(campaign_id, platform),
                )
            )
        session.commit()
        return self.get(session, campaign_id)

    @staticmethod
    def get(session: Session, campaign_id: str) -> Campaign:
        query = (
            select(Campaign)
            .where(Campaign.id == campaign_id)
            .options(selectinload(Campaign.blog_post), selectinload(Campaign.social_posts))
        )
        campaign = session.scalar(query)
        if not campaign:
            raise LookupError("Campaign not found")
        return campaign

    @staticmethod
    def list(session: Session, limit: int = 100) -> list[Campaign]:
        query = (
            select(Campaign)
            .options(selectinload(Campaign.blog_post), selectinload(Campaign.social_posts))
            .order_by(Campaign.created_at.desc())
            .limit(limit)
        )
        return list(session.scalars(query).unique())

    @staticmethod
    def publish_now(session: Session, campaign: Campaign) -> Campaign:
        now = datetime.now(timezone.utc)
        for post in campaign.social_posts:
            if post.status in {SocialPostStatus.QUEUED.value, SocialPostStatus.RETRY_SCHEDULED.value}:
                post.next_attempt_at = now
                post.scheduled_at = min(as_utc(post.scheduled_at), now)
        campaign.scheduled_at = min(as_utc(campaign.scheduled_at), now)
        session.commit()
        return campaign

    @staticmethod
    def reschedule(session: Session, campaign: Campaign, scheduled_at: datetime) -> Campaign:
        if any(p.status not in {SocialPostStatus.QUEUED.value, SocialPostStatus.RETRY_SCHEDULED.value} for p in campaign.social_posts):
            raise ValueError("Only campaigns that have not started can be rescheduled")
        instant = scheduled_at.astimezone(timezone.utc)
        campaign.scheduled_at = instant
        for post in campaign.social_posts:
            post.scheduled_at = instant
            post.next_attempt_at = instant
        session.commit()
        return campaign


def to_campaign_read(campaign: Campaign, settings: Settings) -> CampaignRead:
    posts = [
        SocialPostRead(
            id=post.id,
            platform=post.platform,
            caption=post.caption,
            image_url=f"/media/campaigns/{campaign.id}/{post.platform}.jpg",
            scheduled_at=as_utc(post.scheduled_at),
            next_attempt_at=as_utc(post.next_attempt_at),
            status=post.status,
            idempotency_key=post.idempotency_key,
            external_post_id=post.external_post_id,
            publish_attempt_count=post.publish_attempt_count,
            max_attempts=settings.max_publish_attempts,
            last_error_safe=post.last_error_safe,
            published_at=as_utc(post.published_at) if post.published_at else None,
        )
        for post in sorted(campaign.social_posts, key=lambda item: item.platform)
    ]
    return CampaignRead(
        id=campaign.id,
        blog_post_id=campaign.blog_post_id,
        title=campaign.blog_post.title,
        article_url=campaign.blog_post.url,
        scheduled_at=as_utc(campaign.scheduled_at),
        status=campaign.status,
        created_at=as_utc(campaign.created_at),
        updated_at=as_utc(campaign.updated_at),
        social_posts=posts,
    )
