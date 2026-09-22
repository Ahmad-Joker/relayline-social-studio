from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.database import get_db
from app.db.models import BlogPost, uuid_str
from app.schemas.blog_post import BlogPostRead, BlogPostSeed
from app.services.image_service import ImageService, InvalidImageError

router = APIRouter(prefix="/blog-posts", tags=["blog posts"])


async def _read_limited(upload: UploadFile, maximum: int) -> bytes:
    data = await upload.read(maximum + 1)
    if len(data) > maximum:
        raise HTTPException(status_code=413, detail=f"Image exceeds {maximum} bytes")
    return data


@router.post("", response_model=BlogPostRead, status_code=status.HTTP_201_CREATED)
async def create_blog_post(
    title: str = Form(...),
    body: str = Form(...),
    url: str = Form(...),
    image: UploadFile = File(...),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> BlogPost:
    try:
        validated = BlogPostSeed(title=title, body=body, url=url)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors(include_url=False)) from exc
    payload = await _read_limited(image, settings.upload_max_bytes)
    image_service = ImageService()
    try:
        extension = image_service.validate_bytes(payload)
    except InvalidImageError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    blog_id = uuid_str()
    path = settings.uploads_dir / f"{blog_id}.{extension}"
    path.write_bytes(payload)
    post = BlogPost(id=blog_id, title=validated.title, body=validated.body, url=str(validated.url), source_image_path=str(path))
    session.add(post)
    session.commit()
    session.refresh(post)
    return post


@router.get("", response_model=list[BlogPostRead])
def list_blog_posts(session: Session = Depends(get_db)) -> list[BlogPost]:
    return list(session.scalars(select(BlogPost).order_by(BlogPost.created_at.desc()).limit(100)))


@router.get("/{blog_post_id}", response_model=BlogPostRead)
def get_blog_post(blog_post_id: str, session: Session = Depends(get_db)) -> BlogPost:
    post = session.get(BlogPost, blog_post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Blog post not found")
    return post

