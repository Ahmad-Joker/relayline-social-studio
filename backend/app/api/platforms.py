from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.encryption import TokenCipher
from app.core.enums import Platform
from app.db.database import get_db
from app.db.models import PlatformAccount
from app.services.credential_service import CredentialService

router = APIRouter(prefix="/platform-accounts", tags=["platform accounts"])


class AccountConnect(BaseModel):
    platform: Platform
    external_account_id: str = Field(min_length=1, max_length=255)
    display_name: str = Field(min_length=1, max_length=255)
    access_token: str = Field(min_length=1, max_length=4096)


class AccountRead(BaseModel):
    id: str
    platform: Platform
    external_account_id: str
    display_name: str
    credentials_encrypted: bool = True


@router.post("", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def connect_account(data: AccountConnect, session: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> AccountRead:
    try:
        account = CredentialService(TokenCipher(settings.token_encryption_key)).upsert(
            session,
            platform=data.platform,
            external_account_id=data.external_account_id,
            display_name=data.display_name,
            token=data.access_token,
        )
    except ValueError as exc:
        raise HTTPException(status_code=503, detail="Token encryption is not configured") from exc
    return AccountRead(id=account.id, platform=account.platform, external_account_id=account.external_account_id, display_name=account.display_name)


@router.get("", response_model=list[AccountRead])
def list_accounts(session: Session = Depends(get_db)) -> list[AccountRead]:
    accounts = list(session.scalars(select(PlatformAccount).order_by(PlatformAccount.platform)))
    return [AccountRead(id=a.id, platform=a.platform, external_account_id=a.external_account_id, display_name=a.display_name) for a in accounts]

