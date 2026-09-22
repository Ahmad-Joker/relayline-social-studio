import base64
import logging

from app.core.encryption import TokenCipher
from app.core.enums import Platform
from app.db.models import OAuthToken
from app.services.credential_service import CredentialService


def test_token_round_trip_uses_fresh_nonce_and_ciphertext():
    cipher = TokenCipher(base64.urlsafe_b64encode(b"a" * 32).decode())
    first = cipher.encrypt("sensitive-token")
    second = cipher.encrypt("sensitive-token")
    assert cipher.decrypt(first.ciphertext, first.nonce) == "sensitive-token"
    assert first.nonce != second.nonce
    assert first.ciphertext != second.ciphertext
    assert b"sensitive-token" not in first.ciphertext


def test_database_never_stores_plaintext_token(session, settings, caplog):
    plaintext = "oauth-super-secret-value"
    service = CredentialService(TokenCipher(settings.token_encryption_key))
    with caplog.at_level(logging.INFO):
        service.upsert(
            session,
            platform=Platform.INSTAGRAM,
            external_account_id="fake-1",
            display_name="Demo",
            token=plaintext,
        )
    stored = session.query(OAuthToken).one()
    assert plaintext.encode() not in stored.ciphertext
    assert service.token_for(session, Platform.INSTAGRAM.value) == plaintext
    assert plaintext not in caplog.text

