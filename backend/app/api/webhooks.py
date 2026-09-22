from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.database import get_db
from app.services.webhook_service import InvalidWebhook, WebhookService

router = APIRouter(prefix="/webhook", tags=["webhooks"])


@router.post("/social-delivery")
async def social_delivery(
    request: Request,
    x_social_signature: str | None = Header(default=None),
    x_social_timestamp: str | None = Header(default=None),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, str | bool]:
    body = await request.body()
    try:
        result = WebhookService(settings).handle(session, body, x_social_signature, x_social_timestamp)
    except InvalidWebhook as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "accepted", "duplicate": result.duplicate, "social_post_id": result.social_post_id}

