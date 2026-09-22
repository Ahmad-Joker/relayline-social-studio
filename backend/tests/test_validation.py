from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.core.enums import Platform
from app.integrations.fake_social_client import FakeSocialClient
from app.publishing.base import SocialPublisher
from app.publishing.instagram import FakeInstagramPublisher
from app.publishing.x import FakeXPublisher
from app.schemas.campaign import CampaignCreate


def test_campaign_rejects_unknown_platform():
    with pytest.raises(ValidationError):
        CampaignCreate(
            blog_post_id="a" * 36,
            platforms=["facebook"],
            scheduled_at=datetime.now(timezone.utc),
        )


def test_campaign_rejects_naive_schedule():
    with pytest.raises(ValidationError, match="timezone"):
        CampaignCreate(
            blog_post_id="a" * 36,
            platforms=[Platform.X],
            scheduled_at=datetime.now(),
        )


def test_platform_adapters_implement_shared_contract():
    client = FakeSocialClient("http://fake.invalid")
    try:
        instagram = FakeInstagramPublisher(client)
        x_publisher = FakeXPublisher(client)
        assert isinstance(instagram, SocialPublisher)
        assert isinstance(x_publisher, SocialPublisher)
        assert instagram.platform == Platform.INSTAGRAM.value
        assert x_publisher.platform == Platform.X.value
    finally:
        client.close()

