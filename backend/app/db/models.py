from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, Integer, LargeBinary, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import AttemptOutcome, CampaignStatus, Platform, SocialPostStatus
from app.db.database import Base


def uuid_str() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class BlogPost(TimestampMixin, Base):
    __tablename__ = "blog_posts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    source_image_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    campaigns: Mapped[list[Campaign]] = relationship(back_populates="blog_post", cascade="all, delete-orphan")


class Campaign(TimestampMixin, Base):
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    blog_post_id: Mapped[str] = mapped_column(ForeignKey("blog_posts.id", ondelete="CASCADE"), nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default=CampaignStatus.QUEUED.value, nullable=False, index=True)
    blog_post: Mapped[BlogPost] = relationship(back_populates="campaigns")
    social_posts: Mapped[list[SocialPost]] = relationship(back_populates="campaign", cascade="all, delete-orphan")


class SocialPost(TimestampMixin, Base):
    __tablename__ = "social_posts"
    __table_args__ = (
        UniqueConstraint("campaign_id", "platform", name="uq_social_post_campaign_platform"),
        UniqueConstraint("idempotency_key", name="uq_social_post_idempotency_key"),
        Index("ix_social_posts_due", "status", "next_attempt_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    campaign_id: Mapped[str] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    platform: Mapped[str] = mapped_column(String(32), nullable=False)
    caption: Mapped[str] = mapped_column(Text, nullable=False)
    image_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    next_attempt_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=SocialPostStatus.QUEUED.value, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False)
    external_post_id: Mapped[str | None] = mapped_column(String(255))
    publish_attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error_safe: Mapped[str | None] = mapped_column(String(500))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    campaign: Mapped[Campaign] = relationship(back_populates="social_posts")
    attempts: Mapped[list[PublishAttempt]] = relationship(back_populates="social_post", cascade="all, delete-orphan")


class PlatformAccount(TimestampMixin, Base):
    __tablename__ = "platform_accounts"
    __table_args__ = (UniqueConstraint("platform", "external_account_id", name="uq_platform_external_account"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    platform: Mapped[str] = mapped_column(String(32), nullable=False)
    external_account_id: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    token: Mapped[OAuthToken] = relationship(back_populates="account", uselist=False, cascade="all, delete-orphan")


class OAuthToken(TimestampMixin, Base):
    __tablename__ = "oauth_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    platform_account_id: Mapped[str] = mapped_column(ForeignKey("platform_accounts.id", ondelete="CASCADE"), unique=True)
    ciphertext: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    nonce: Mapped[bytes] = mapped_column(LargeBinary(12), nullable=False)
    key_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    account: Mapped[PlatformAccount] = relationship(back_populates="token")


class ProcessedWebhook(Base):
    __tablename__ = "processed_webhooks"

    event_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    payload_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    social_post_id: Mapped[str] = mapped_column(ForeignKey("social_posts.id", ondelete="CASCADE"), nullable=False)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class PublishAttempt(Base):
    __tablename__ = "publish_attempts"
    __table_args__ = (UniqueConstraint("social_post_id", "attempt_number", name="uq_publish_attempt_number"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    social_post_id: Mapped[str] = mapped_column(ForeignKey("social_posts.id", ondelete="CASCADE"), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False)
    safe_detail: Mapped[str | None] = mapped_column(String(500))
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    social_post: Mapped[SocialPost] = relationship(back_populates="attempts")

