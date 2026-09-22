import re
from dataclasses import dataclass
from typing import Protocol

from app.captions.brand import BRAND_VOICE
from app.captions.instagram import INSTAGRAM_RULES
from app.captions.x import X_RULES
from app.core.enums import Platform


@dataclass(frozen=True)
class CaptionContext:
    title: str
    summary: str
    url: str
    brand_voice: str
    platform_rules: str


class CaptionGenerator(Protocol):
    def generate(self, platform: Platform, context: CaptionContext) -> str: ...


class TemplateCaptionGenerator:
    def generate(self, platform: Platform, context: CaptionContext) -> str:
        if platform is Platform.INSTAGRAM:
            return (
                f"{context.title}\n\n{context.summary}\n\n"
                f"Read the full story: {context.url}\n\n#NewArticle #Insights"
            )
        prefix = f"{context.title}: {context.summary}"
        suffix = f" {context.url}"
        room = 280 - len(suffix)
        if len(prefix) > room:
            prefix = prefix[: max(0, room - 1)].rstrip() + "…"
        return prefix + suffix


class CaptionComposer:
    def __init__(self, generator: CaptionGenerator | None = None):
        self.generator = generator or TemplateCaptionGenerator()

    @staticmethod
    def summarize(body: str, max_chars: int = 220) -> str:
        clean = re.sub(r"\s+", " ", body).strip()
        if len(clean) <= max_chars:
            return clean
        excerpt = clean[: max_chars + 1]
        boundary = excerpt.rfind(" ")
        return excerpt[: boundary if boundary > 80 else max_chars].rstrip(" ,.;:") + "…"

    def compose(self, platform: Platform, *, title: str, body: str, url: str) -> str:
        rules = INSTAGRAM_RULES if platform is Platform.INSTAGRAM else X_RULES
        context = CaptionContext(title, self.summarize(body), url, BRAND_VOICE, rules)
        return self.generator.generate(platform, context)

