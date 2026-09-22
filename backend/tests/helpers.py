from datetime import datetime, timezone

from PIL import Image

from app.core.enums import Platform
from app.db.models import BlogPost
from app.schemas.campaign import CampaignCreate
from app.services.campaign_service import CampaignService


def make_campaign(session, settings, tmp_path, platforms=(Platform.INSTAGRAM, Platform.X)):
    source = tmp_path / "source.png"
    Image.new("RGB", (2200, 1200), "#74d3ae").save(source)
    blog = BlogPost(
        title="A practical guide to durable work",
        body="Reliable systems preserve intent in the database and make every retry safe. This article explains leases, idempotency, and trusted delivery events.",
        url="https://example.com/durable-work",
        source_image_path=str(source),
    )
    session.add(blog)
    session.commit()
    session.refresh(blog)
    campaign = CampaignService(settings).create(
        session,
        CampaignCreate(blog_post_id=blog.id, platforms=list(platforms), scheduled_at=datetime.now(timezone.utc)),
    )
    return campaign

