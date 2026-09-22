import json
import time

import pytest

from app.core.enums import Platform, SocialPostStatus
from app.db.models import ProcessedWebhook, SocialPost
from app.services.webhook_service import InvalidWebhook, WebhookService, sign_webhook
from tests.helpers import make_campaign


def prepare_post(session, settings, tmp_path):
    campaign = make_campaign(session, settings, tmp_path, (Platform.INSTAGRAM,))
    post = campaign.social_posts[0]
    post.status = SocialPostStatus.AWAITING_DELIVERY.value
    post.external_post_id = "external-instagram"
    session.commit()
    return post


def signed_payload(settings, post, event_id="evt-1"):
    body = json.dumps(
        {
            "event_id": event_id,
            "social_post_id": post.id,
            "external_post_id": post.external_post_id,
            "status": "published",
        },
        separators=(",", ":"),
    ).encode()
    timestamp = str(int(time.time()))
    return body, timestamp, sign_webhook(settings.social_webhook_secret, timestamp, body)


def test_forged_webhook_is_rejected_without_status_change(session, settings, tmp_path):
    post = prepare_post(session, settings, tmp_path)
    body, timestamp, _ = signed_payload(settings, post)
    with pytest.raises(InvalidWebhook, match="signature"):
        WebhookService(settings).handle(session, body, "sha256=forged", timestamp)
    session.refresh(post)
    assert post.status == SocialPostStatus.AWAITING_DELIVERY.value
    assert session.query(ProcessedWebhook).count() == 0


def test_valid_webhook_publishes_and_replay_is_idempotent(session, settings, tmp_path):
    post = prepare_post(session, settings, tmp_path)
    body, timestamp, signature = signed_payload(settings, post)
    first = WebhookService(settings).handle(session, body, signature, timestamp)
    second = WebhookService(settings).handle(session, body, signature, timestamp)
    session.refresh(post)
    assert first.duplicate is False
    assert second.duplicate is True
    assert post.status == SocialPostStatus.PUBLISHED.value
    assert post.published_at is not None
    assert session.query(ProcessedWebhook).count() == 1


def test_modified_body_with_old_signature_is_rejected(session, settings, tmp_path):
    post = prepare_post(session, settings, tmp_path)
    body, timestamp, signature = signed_payload(settings, post)
    modified = body.replace(b"published", b"failed")
    with pytest.raises(InvalidWebhook, match="signature"):
        WebhookService(settings).handle(session, modified, signature, timestamp)

