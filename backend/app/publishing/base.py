from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.integrations.fake_social_client import ClientPublishResult


@dataclass(frozen=True)
class PublishRequest:
    social_post_id: str
    caption: str
    image_bytes: bytes
    idempotency_key: str
    access_token: str


class SocialPublisher(ABC):
    platform: str

    @abstractmethod
    def publish(self, request: PublishRequest) -> ClientPublishResult:
        raise NotImplementedError

    @abstractmethod
    def validate_credentials(self, access_token: str) -> bool:
        raise NotImplementedError

    def parse_delivery_event(self, payload: dict) -> dict:
        return payload

