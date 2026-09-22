from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.encryption import TokenCipher
from app.core.enums import Platform
from app.db.models import OAuthToken, PlatformAccount


class CredentialService:
    def __init__(self, cipher: TokenCipher):
        self.cipher = cipher

    def upsert(self, session: Session, *, platform: Platform, external_account_id: str, display_name: str, token: str) -> PlatformAccount:
        query = select(PlatformAccount).where(
            PlatformAccount.platform == platform.value,
            PlatformAccount.external_account_id == external_account_id,
        )
        account = session.scalar(query)
        if not account:
            account = PlatformAccount(platform=platform.value, external_account_id=external_account_id, display_name=display_name)
            session.add(account)
            session.flush()
        sealed = self.cipher.encrypt(token)
        if account.token:
            account.token.ciphertext = sealed.ciphertext
            account.token.nonce = sealed.nonce
        else:
            account.token = OAuthToken(ciphertext=sealed.ciphertext, nonce=sealed.nonce)
        account.display_name = display_name
        session.commit()
        return account

    def token_for(self, session: Session, platform: str) -> str:
        query = select(OAuthToken).join(PlatformAccount).where(PlatformAccount.platform == platform).limit(1)
        token = session.scalar(query)
        if not token:
            raise LookupError(f"No platform account configured for {platform}")
        return self.cipher.decrypt(token.ciphertext, token.nonce)

