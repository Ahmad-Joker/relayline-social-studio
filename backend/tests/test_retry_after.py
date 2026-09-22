from datetime import datetime, timedelta, timezone
from email.utils import format_datetime

from app.integrations.fake_social_client import parse_retry_after


def test_retry_after_supports_seconds_and_http_date():
    now = datetime.now(timezone.utc).replace(microsecond=0)
    assert parse_retry_after("30", now=now) == 30
    assert parse_retry_after(format_datetime(now + timedelta(seconds=45)), now=now) == 45


def test_retry_after_is_safe_and_bounded():
    assert parse_retry_after("nonsense", maximum=120) == 60
    assert parse_retry_after("99999", maximum=120) == 120
    assert parse_retry_after("0") == 1

