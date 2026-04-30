"""Encrypt / decrypt at-rest IdP secret blobs stored in Organization.identityConfig."""

from __future__ import annotations

import base64
import hashlib
from typing import ClassVar

from nims.config import get_settings

try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError:  # pragma: no cover
    Fernet = None  # type: ignore[assignment, misc]
    InvalidToken = Exception  # type: ignore[assignment, misc]


def _fernet() -> Fernet:
    if Fernet is None:  # pragma: no cover
        raise RuntimeError("cryptography package required for IdP secret storage in the database")
    settings = get_settings()
    raw = (getattr(settings, "identity_encryption_key", None) or settings.jwt_secret) + "|nims-identity-v1"
    digest = hashlib.sha256(raw.encode("utf-8")).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_secret(plain: str) -> str:
    return _fernet().encrypt(plain.encode("utf-8")).decode("ascii")


def decrypt_secret(token: str) -> str | None:
    try:
        r = _fernet().decrypt(token.encode("ascii"))
        return r.decode("utf-8")
    except (InvalidToken, TypeError, ValueError):
        return None


# Marker prefix so we can tell encrypted vs legacy accidental plain (reject plain on read for secrets)
PREFIX: ClassVar[str] = "f1:"


def pack_encrypted(plain: str) -> str:
    return PREFIX + encrypt_secret(plain)


def unpack_encrypted(stored: str | None) -> str | None:
    if not stored or not isinstance(stored, str):
        return None
    if not stored.startswith(PREFIX):
        return None
    return decrypt_secret(stored.removeprefix(PREFIX))
