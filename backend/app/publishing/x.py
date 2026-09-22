from app.integrations.fake_social_client import ClientPublishResult, FakeSocialClient
from app.publishing.base import PublishRequest, SocialPublisher


class FakeXPublisher(SocialPublisher):
    platform = "x"

    def __init__(self, client: FakeSocialClient):
        self.client = client

    def publish(self, request: PublishRequest) -> ClientPublishResult:
        return self.client.publish(platform=self.platform, **request.__dict__)

    def validate_credentials(self, access_token: str) -> bool:
        return bool(access_token)

