import base64
import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("TOKEN_ENCRYPTION_KEY", base64.urlsafe_b64encode(b"t" * 32).decode())

from app.core.config import Settings  # noqa: E402
from app.db.database import Base  # noqa: E402
from app.db import models  # noqa: E402,F401


@pytest.fixture
def session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as db:
        yield db
    Base.metadata.drop_all(engine)


@pytest.fixture
def settings(tmp_path):
    return Settings(
        database_url="sqlite://",
        token_encryption_key=base64.urlsafe_b64encode(b"k" * 32).decode(),
        social_webhook_secret="test-webhook-secret",
        data_dir=tmp_path,
        public_api_url="http://testserver",
        max_publish_attempts=4,
        publish_lease_seconds=10,
    )

