from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.enums import CampaignStatus, Platform, SocialPostStatus


class CampaignCreate(BaseModel):
    blog_post_id: str = Field(min_length=36, max_length=36)
    platforms: list[Platform] = Field(min_length=1, max_length=2)
    scheduled_at: datetime

    @field_validator("platforms")
    @classmethod
    def unique_platforms(cls, value: list[Platform]) -> list[Platform]:
        if len(set(value)) != len(value):
            raise ValueError("platforms must be unique")
        return value

    @field_validator("scheduled_at")
    @classmethod
    def timezone_required(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("scheduled_at must include a timezone")
        return value


class RescheduleRequest(BaseModel):
    scheduled_at: datetime

    @field_validator("scheduled_at")
    @classmethod
    def timezone_required(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("scheduled_at must include a timezone")
        return value


class SocialPostRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    platform: Platform
    caption: str
    image_url: str
    scheduled_at: datetime
    next_attempt_at: datetime
    status: SocialPostStatus
    idempotency_key: str
    external_post_id: str | None
    publish_attempt_count: int
    max_attempts: int
    last_error_safe: str | None
    published_at: datetime | None


class CampaignRead(BaseModel):
    id: str
    blog_post_id: str
    title: str
    article_url: str
    scheduled_at: datetime
    status: CampaignStatus
    created_at: datetime
    updated_at: datetime
    social_posts: list[SocialPostRead]


class DashboardRead(BaseModel):
    total: int
    scheduled: int
    publishing: int
    published: int
    failed: int
    recent_campaigns: list[CampaignRead]

