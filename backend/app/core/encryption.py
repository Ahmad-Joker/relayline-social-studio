import base64
import os
from dataclasses import dataclass

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

AAD = b"relayline-oauth-v1"


@dataclass(frozen=True)
class EncryptedValue:
    ciphertext: bytes
    nonce: bytes


class TokenCipher:
    def __init__(self, encoded_key: str):
        if not encoded_key:
            raise ValueError("TOKEN_ENCRYPTION_KEY is required")
        try:
            key = base64.urlsafe_b64decode(encoded_key.encode("ascii"))
        except (ValueError, UnicodeError) as exc:
            raise ValueError("TOKEN_ENCRYPTION_KEY must be URL-safe base64") from exc
        if len(key) != 32:
            raise ValueError("TOKEN_ENCRYPTION_KEY must decode to exactly 32 bytes")
        self._cipher = AESGCM(key)

    def encrypt(self, plaintext: str) -> EncryptedValue:
        nonce = os.urandom(12)
        return EncryptedValue(self._cipher.encrypt(nonce, plaintext.encode("utf-8"), AAD), nonce)

    def decrypt(self, ciphertext: bytes, nonce: bytes) -> str:
        return self._cipher.decrypt(nonce, ciphertext, AAD).decode("utf-8")


def generate_key() -> str:
    return base64.urlsafe_b64encode(AESGCM.generate_key(bit_length=256)).decode("ascii")

