from enum import StrEnum


class Platform(StrEnum):
    INSTAGRAM = "instagram"
    X = "x"


class CampaignStatus(StrEnum):
    DRAFT = "draft"
    QUEUED = "queued"
    PUBLISHING = "publishing"
    PARTIALLY_PUBLISHED = "partially_published"
    PUBLISHED = "published"
    FAILED = "failed"


class SocialPostStatus(StrEnum):
    QUEUED = "queued"
    PUBLISHING = "publishing"
    RETRY_SCHEDULED = "retry_scheduled"
    AWAITING_DELIVERY = "awaiting_delivery"
    PUBLISHED = "published"
    FAILED = "failed"


class AttemptOutcome(StrEnum):
    ACKNOWLEDGED = "acknowledged"
    RATE_LIMITED = "rate_limited"
    RETRYABLE_ERROR = "retryable_error"
    PERMANENT_ERROR = "permanent_error"

