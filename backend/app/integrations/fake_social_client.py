from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import httpx


class PublishError(RuntimeError):
    pass


class RetryablePublishError(PublishError):
    pass


class PermanentPublishError(PublishError):
    pass


class RateLimitError(PublishError):
    def __init__(self, retry_after_seconds: int):
        super().__init__("Platform rate limit reached")
        self.retry_after_seconds = retry_after_seconds


def parse_retry_after(value: str | None, *, now: datetime | None = None, maximum: int = 3600) -> int:
    if not value:
        return min(60, maximum)
    try:
        return max(1, min(int(value.strip()), maximum))
    except ValueError:
        try:
            target = parsedate_to_datetime(value)
            if target.tzinfo is None:
                target = target.replace(tzinfo=timezone.utc)
            current = now or datetime.now(timezone.utc)
            return max(1, min(int((target - current).total_seconds()), maximum))
        except (TypeError, ValueError, OverflowError):
            return min(60, maximum)


@dataclass(frozen=True)
class ClientPublishResult:
    external_post_id: str


class FakeSocialClient:
    """One redacting HTTP boundary for the supplied FlyRank fake platform.

    The server was absent from the supplied materials. Endpoint and response mapping
    are kept here so its exact contract can be aligned without touching domain code.
    """

    def __init__(self, base_url: str, *, retry_max_seconds: int = 3600, transport: httpx.BaseTransport | None = None):
        self.retry_max_seconds = retry_max_seconds
        self._client = httpx.Client(base_url=base_url, timeout=httpx.Timeout(10, connect=5), transport=transport)

    def close(self) -> None:
        self._client.close()

    def publish(
        self,
        *,
        platform: str,
        caption: str,
        image_bytes: bytes,
        access_token: str,
        idempotency_key: str,
        social_post_id: str,
    ) -> ClientPublishResult:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Idempotency-Key": idempotency_key,
        }
        data = {"platform": platform, "caption": caption, "client_reference": social_post_id}
        files = {"image": (f"{platform}.jpg", image_bytes, "image/jpeg")}
        try:
            response = self._client.post("/api/posts", headers=headers, data=data, files=files)
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            raise RetryablePublishError("Temporary platform connection failure") from exc
        if response.status_code == 429:
            raise RateLimitError(parse_retry_after(response.headers.get("Retry-After"), maximum=self.retry_max_seconds))
        if response.status_code >= 500:
            raise RetryablePublishError(f"Platform temporarily unavailable ({response.status_code})")
        if response.status_code >= 400:
            raise PermanentPublishError(f"Platform rejected publish request ({response.status_code})")
        try:
            payload = response.json()
            external_id = str(payload["id"])
        except (ValueError, KeyError, TypeError) as exc:
            raise RetryablePublishError("Platform returned an invalid acknowledgement") from exc
        return ClientPublishResult(external_post_id=external_id)

