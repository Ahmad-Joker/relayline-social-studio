from datetime import datetime

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field


class BlogPostRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    body: str
    url: AnyHttpUrl
    created_at: datetime
    updated_at: datetime


class BlogPostSeed(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    body: str = Field(min_length=20, max_length=100_000)
    url: AnyHttpUrl

