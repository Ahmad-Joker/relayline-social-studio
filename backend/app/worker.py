import logging
import signal
import time

from app.core.config import get_settings
from app.core.encryption import TokenCipher
from app.core.logging import configure_logging
from app.db.database import SessionLocal
from app.integrations.fake_social_client import FakeSocialClient
from app.publishing.instagram import FakeInstagramPublisher
from app.publishing.x import FakeXPublisher
from app.services.credential_service import CredentialService
from app.services.publishing_service import PublishingService

logger = logging.getLogger(__name__)
running = True


def stop(*_: object) -> None:
    global running
    running = False


def build_service() -> tuple[PublishingService, FakeSocialClient]:
    settings = get_settings()
    client = FakeSocialClient(settings.fake_social_base_url, retry_max_seconds=settings.retry_max_seconds)
    credentials = CredentialService(TokenCipher(settings.token_encryption_key))
    publishers = {
        "instagram": FakeInstagramPublisher(client),
        "x": FakeXPublisher(client),
    }
    return PublishingService(settings, credentials, publishers), client


def run() -> None:
    configure_logging()
    settings = get_settings()
    service, client = build_service()
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    logger.info("worker_started")
    try:
        while running:
            with SessionLocal() as session:
                post_id = service.claim_due(session)
            if post_id:
                with SessionLocal() as session:
                    service.process_claimed(session, post_id)
            else:
                time.sleep(settings.worker_poll_seconds)
    finally:
        client.close()
        logger.info("worker_stopped")


if __name__ == "__main__":
    run()

