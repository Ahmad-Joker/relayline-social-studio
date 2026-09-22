import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.enums import SocialPostStatus
from app.db.models import ProcessedWebhook, SocialPost
from app.services.publishing_service import recompute_campaign_status


class InvalidWebhook(ValueError):
    pass


@dataclass(frozen=True)
class WebhookResult:
    duplicate: bool
    social_post_id: str


def sign_webhook(secret: str, timestamp: str, body: bytes) -> str:
    digest = hmac.new(secret.encode(), timestamp.encode() + b"." + body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


class WebhookService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def handle(self, session: Session, body: bytes, signature: str | None, timestamp: str | None) -> WebhookResult:
        if not signature or not timestamp:
            raise InvalidWebhook("Missing webhook signature")
        try:
            sent_at = int(timestamp)
        except ValueError as exc:
            raise InvalidWebhook("Invalid webhook timestamp") from exc
        if abs(int(time.time()) - sent_at) > self.settings.webhook_tolerance_seconds:
            raise InvalidWebhook("Webhook timestamp outside tolerance")
        expected = sign_webhook(self.settings.social_webhook_secret, timestamp, body)
        if not hmac.compare_digest(expected, signature):
            raise InvalidWebhook("Invalid webhook signature")
        try:
            payload = json.loads(body)
            event_id = str(payload["event_id"])
            post_id = str(payload["social_post_id"])
            status = str(payload["status"]).lower()
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise InvalidWebhook("Malformed webhook payload") from exc
        existing = session.get(ProcessedWebhook, event_id)
        if existing:
            return WebhookResult(duplicate=True, social_post_id=existing.social_post_id)
        post = session.get(SocialPost, post_id)
        if not post:
            raise InvalidWebhook("Unknown social post")
        external_id = payload.get("external_post_id")
        if external_id and post.external_post_id and str(external_id) != post.external_post_id:
            raise InvalidWebhook("External post identifier mismatch")
        if status == "published":
            if post.status not in {SocialPostStatus.AWAITING_DELIVERY.value, SocialPostStatus.PUBLISHED.value}:
                raise InvalidWebhook("Social post is not awaiting delivery")
            post.status = SocialPostStatus.PUBLISHED.value
            post.published_at = datetime.now(timezone.utc)
            post.last_error_safe = None
        elif status == "failed":
            post.status = SocialPostStatus.FAILED.value
            post.last_error_safe = "Platform reported delivery failure"
        else:
            raise InvalidWebhook("Unsupported delivery status")
        session.add(ProcessedWebhook(event_id=event_id, payload_digest=hashlib.sha256(body).hexdigest(), social_post_id=post.id))
        recompute_campaign_status(session, post.campaign_id)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            return WebhookResult(duplicate=True, social_post_id=post.id)
        return WebhookResult(duplicate=False, social_post_id=post.id)
