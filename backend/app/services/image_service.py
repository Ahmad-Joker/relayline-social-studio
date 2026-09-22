import io
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.enums import Platform

SPECS = {
    Platform.INSTAGRAM: (1080, 1080),
    Platform.X: (1600, 900),
}
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}


class InvalidImageError(ValueError):
    pass


class ImageService:
    def validate_bytes(self, data: bytes) -> str:
        try:
            with Image.open(io.BytesIO(data)) as image:
                image.verify()
                if image.format not in ALLOWED_FORMATS:
                    raise InvalidImageError("Image must be JPEG, PNG, or WebP")
                return image.format.lower()
        except (UnidentifiedImageError, OSError) as exc:
            raise InvalidImageError("File is not a valid supported image") from exc

    def create_variants(self, source: Path, output_dir: Path) -> dict[Platform, Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        try:
            with Image.open(source) as original:
                if original.format not in ALLOWED_FORMATS:
                    raise InvalidImageError("Image must be JPEG, PNG, or WebP")
                normalized = ImageOps.exif_transpose(original).convert("RGB")
                outputs: dict[Platform, Path] = {}
                for platform, dimensions in SPECS.items():
                    variant = ImageOps.fit(normalized, dimensions, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
                    target = output_dir / f"{platform.value}.jpg"
                    variant.save(target, "JPEG", quality=90, optimize=True, progressive=True)
                    outputs[platform] = target
                return outputs
        except (UnidentifiedImageError, OSError) as exc:
            raise InvalidImageError("Source image cannot be processed") from exc

