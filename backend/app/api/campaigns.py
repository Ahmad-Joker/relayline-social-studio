from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.enums import CampaignStatus
from app.db.database import get_db
from app.schemas.campaign import CampaignCreate, CampaignRead, DashboardRead, RescheduleRequest
from app.services.campaign_service import CampaignService, to_campaign_read

router = APIRouter(tags=["campaigns"])


def _service(settings: Settings) -> CampaignService:
    return CampaignService(settings)


@router.post("/campaigns", response_model=CampaignRead, status_code=status.HTTP_201_CREATED)
def create_campaign(data: CampaignCreate, session: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> CampaignRead:
    try:
        campaign = _service(settings).create(session, data)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return to_campaign_read(campaign, settings)


@router.get("/campaigns", response_model=list[CampaignRead])
def list_campaigns(
    limit: int = Query(default=100, ge=1, le=200),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> list[CampaignRead]:
    return [to_campaign_read(item, settings) for item in CampaignService.list(session, limit)]


@router.get("/campaigns/{campaign_id}", response_model=CampaignRead)
def get_campaign(campaign_id: str, session: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> CampaignRead:
    try:
        return to_campaign_read(CampaignService.get(session, campaign_id), settings)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/campaigns/{campaign_id}/posts", response_model=CampaignRead)
def get_campaign_posts(campaign_id: str, session: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> CampaignRead:
    return get_campaign(campaign_id, session, settings)


@router.post("/campaigns/{campaign_id}/publish", response_model=CampaignRead)
def publish_campaign(campaign_id: str, session: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> CampaignRead:
    try:
        campaign = CampaignService.get(session, campaign_id)
        CampaignService.publish_now(session, campaign)
        return to_campaign_read(CampaignService.get(session, campaign_id), settings)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/campaigns/{campaign_id}/reschedule", response_model=CampaignRead)
def reschedule_campaign(
    campaign_id: str,
    data: RescheduleRequest,
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> CampaignRead:
    try:
        campaign = CampaignService.get(session, campaign_id)
        CampaignService.reschedule(session, campaign, data.scheduled_at)
        return to_campaign_read(CampaignService.get(session, campaign_id), settings)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/dashboard", response_model=DashboardRead)
def dashboard(session: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> DashboardRead:
    campaigns = CampaignService.list(session, 100)
    counts = Counter(item.status for item in campaigns)
    publishing = counts[CampaignStatus.PUBLISHING.value] + counts[CampaignStatus.PARTIALLY_PUBLISHED.value]
    return DashboardRead(
        total=len(campaigns),
        scheduled=counts[CampaignStatus.QUEUED.value],
        publishing=publishing,
        published=counts[CampaignStatus.PUBLISHED.value],
        failed=counts[CampaignStatus.FAILED.value],
        recent_campaigns=[to_campaign_read(item, settings) for item in campaigns[:8]],
    )

