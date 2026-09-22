from PIL import Image
import pytest

from app.captions.brand import BRAND_VOICE
from app.captions.composer import CaptionComposer, CaptionContext, TemplateCaptionGenerator
from app.captions.instagram import INSTAGRAM_RULES
from app.captions.x import X_RULES
from app.core.enums import Platform
from app.services.image_service import ImageService, InvalidImageError


def test_image_variants_have_exact_dimensions_and_valid_format(tmp_path):
    source = tmp_path / "source.png"
    Image.new("RGB", (2100, 900), "#ef8354").save(source)
    outputs = ImageService().create_variants(source, tmp_path / "out")

    with Image.open(outputs[Platform.INSTAGRAM]) as instagram:
        assert instagram.size == (1080, 1080)
        assert instagram.format == "JPEG"
    with Image.open(outputs[Platform.X]) as x_image:
        assert x_image.size == (1600, 900)
        assert x_image.format == "JPEG"


def test_image_pipeline_rejects_unsupported_input(tmp_path):
    source = tmp_path / "not-an-image.txt"
    source.write_text("not image data")
    with pytest.raises(InvalidImageError):
        ImageService().create_variants(source, tmp_path / "out")


def test_caption_composer_is_platform_specific_and_x_is_bounded():
    composer = CaptionComposer()
    kwargs = {
        "title": "Why durable publishing matters",
        "body": "A long article about deterministic retries, idempotency, state machines, and signed delivery events. " * 8,
        "url": "https://example.com/reliability",
    }
    instagram = composer.compose(Platform.INSTAGRAM, **kwargs)
    x_caption = composer.compose(Platform.X, **kwargs)

    assert instagram != x_caption
    assert "#NewArticle" in instagram
    assert kwargs["url"] in x_caption
    assert len(x_caption) <= 280
    assert BRAND_VOICE and INSTAGRAM_RULES and X_RULES


def test_generator_receives_shared_and_platform_fragments():
    captured: list[CaptionContext] = []

    class SpyGenerator(TemplateCaptionGenerator):
        def generate(self, platform, context):
            captured.append(context)
            return super().generate(platform, context)

    composer = CaptionComposer(SpyGenerator())
    composer.compose(Platform.INSTAGRAM, title="Title", body="Body content", url="https://example.com")
    composer.compose(Platform.X, title="Title", body="Body content", url="https://example.com")
    assert captured[0].brand_voice == captured[1].brand_voice == BRAND_VOICE
    assert captured[0].platform_rules == INSTAGRAM_RULES
    assert captured[1].platform_rules == X_RULES

