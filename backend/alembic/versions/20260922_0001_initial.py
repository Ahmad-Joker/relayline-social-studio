"""initial durable campaign schema

Revision ID: 20260922_0001
Revises:
Create Date: 2026-09-22
"""
from alembic import op
import sqlalchemy as sa

revision = "20260922_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "blog_posts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("source_image_path", sa.String(1024), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "campaigns",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("blog_post_id", sa.String(36), sa.ForeignKey("blog_posts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_campaigns_scheduled_at", "campaigns", ["scheduled_at"])
    op.create_index("ix_campaigns_status", "campaigns", ["status"])
    op.create_table(
        "social_posts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("campaign_id", sa.String(36), sa.ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("platform", sa.String(32), nullable=False),
        sa.Column("caption", sa.Text(), nullable=False),
        sa.Column("image_path", sa.String(1024), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("idempotency_key", sa.String(64), nullable=False),
        sa.Column("external_post_id", sa.String(255)),
        sa.Column("publish_attempt_count", sa.Integer(), nullable=False),
        sa.Column("last_error_safe", sa.String(500)),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("lease_until", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("campaign_id", "platform", name="uq_social_post_campaign_platform"),
        sa.UniqueConstraint("idempotency_key", name="uq_social_post_idempotency_key"),
    )
    op.create_index("ix_social_posts_due", "social_posts", ["status", "next_attempt_at"])
    op.create_index("ix_social_posts_lease_until", "social_posts", ["lease_until"])
    op.create_table(
        "platform_accounts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("platform", sa.String(32), nullable=False),
        sa.Column("external_account_id", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("platform", "external_account_id", name="uq_platform_external_account"),
    )
    op.create_table(
        "oauth_tokens",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("platform_account_id", sa.String(36), sa.ForeignKey("platform_accounts.id", ondelete="CASCADE"), unique=True),
        sa.Column("ciphertext", sa.LargeBinary(), nullable=False),
        sa.Column("nonce", sa.LargeBinary(12), nullable=False),
        sa.Column("key_version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "processed_webhooks",
        sa.Column("event_id", sa.String(255), primary_key=True),
        sa.Column("payload_digest", sa.String(64), nullable=False),
        sa.Column("social_post_id", sa.String(36), sa.ForeignKey("social_posts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "publish_attempts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("social_post_id", sa.String(36), sa.ForeignKey("social_posts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("outcome", sa.String(32), nullable=False),
        sa.Column("safe_detail", sa.String(500)),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("social_post_id", "attempt_number", name="uq_publish_attempt_number"),
    )


def downgrade() -> None:
    op.drop_table("publish_attempts")
    op.drop_table("processed_webhooks")
    op.drop_table("oauth_tokens")
    op.drop_table("platform_accounts")
    op.drop_index("ix_social_posts_lease_until", table_name="social_posts")
    op.drop_index("ix_social_posts_due", table_name="social_posts")
    op.drop_table("social_posts")
    op.drop_index("ix_campaigns_status", table_name="campaigns")
    op.drop_index("ix_campaigns_scheduled_at", table_name="campaigns")
    op.drop_table("campaigns")
    op.drop_table("blog_posts")
