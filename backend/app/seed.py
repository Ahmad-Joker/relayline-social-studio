from datetime import datetime, timedelta, timezone

from PIL import Image, ImageDraw
from sqlalchemy import select

from app.core.config import get_settings
from app.core.encryption import TokenCipher
from app.core.enums import Platform
from app.db.database import SessionLocal
from app.db.models import BlogPost
from app.schemas.campaign import CampaignCreate
from app.services.campaign_service import CampaignService
from app.services.credential_service import CredentialService


def seed() -> None:
    settings = get_settings()
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    source = settings.uploads_dir / "demo-source.jpg"
    if not source.exists():
        image = Image.new("RGB", (1800, 1200), "#e7ff70")
        draw = ImageDraw.Draw(image)
        draw.rectangle((100, 100, 1700, 1100), outline="#11241c", width=18)
        draw.text((180, 180), "RELAYLINE / DEMO ARTICLE", fill="#11241c")
        image.save(source, "JPEG", quality=92)
    with SessionLocal() as session:
        blog = session.scalar(select(BlogPost).where(BlogPost.url == "https://example.com/reliable-publishing"))
        if not blog:
            blog = BlogPost(
                title="Reliable publishing is a state machine",
                body="A resilient campaign publisher treats schedules, retries, delivery confirmations, and credentials as explicit durable state. That discipline prevents duplicates and makes recovery predictable.",
                url="https://example.com/reliable-publishing",
                source_image_path=str(source),
            )
            session.add(blog)
            session.commit()
            session.refresh(blog)
        cipher = TokenCipher(settings.token_encryption_key)
        credentials = CredentialService(cipher)
        for platform in Platform:
            credentials.upsert(
                session,
                platform=platform,
                external_account_id=f"fake-{platform.value}-demo",
                display_name=f"Demo {platform.value.title()}",
                token=f"seed-placeholder-{platform.value}-token",
            )
        if not blog.campaigns:
            CampaignService(settings).create(
                session,
                CampaignCreate(
                    blog_post_id=blog.id,
                    platforms=[Platform.INSTAGRAM, Platform.X],
                    scheduled_at=datetime.now(timezone.utc) + timedelta(minutes=10),
                ),
            )
    print("Demo blog, encrypted fake credentials, and scheduled campaign are ready.")


if __name__ == "__main__":
    seed()
