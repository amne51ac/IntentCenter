import uuid
from typing import Annotated

import jwt
from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from nims.auth_context import AuthContext, UserAuth
from nims.config import get_settings
from nims.crypto_util import hash_token
from nims.db import get_db
from nims.models_generated import ApiToken, User
from nims.timeutil import utc_now


def resolve_auth(db: Session, request: Request) -> AuthContext | None:
    settings = get_settings()
    h = request.headers.get("authorization")
    if h and h.startswith("Bearer "):
        raw = h[7:].strip()
        if not raw:
            return None
        token_hash = hash_token(raw)
        tok = db.execute(
            select(ApiToken).where(ApiToken.tokenHash == token_hash).options(joinedload(ApiToken.Organization_))
        ).scalar_one_or_none()
        if tok is None:
            return None
        if tok.expiresAt and tok.expiresAt < utc_now():
            return None
        return AuthContext(organization=tok.Organization_, role=tok.role, api_token=tok)

    raw = request.cookies.get("nims_session")
    if raw:
        try:
            payload = jwt.decode(raw, settings.jwt_secret, algorithms=["HS256"])
            sub = payload.get("sub")
            if not sub:
                return None
            user = db.execute(
                select(User).where(User.id == uuid.UUID(str(sub))).options(joinedload(User.Organization_))
            ).scalar_one_or_none()
            if user is None or user.Organization_.deletedAt is not None:
                return None
            return AuthContext(
                organization=user.Organization_,
                role=user.role,
                user=UserAuth(
                    id=str(user.id),
                    email=user.email,
                    displayName=user.displayName,
                    authProvider=user.authProvider.value,
                ),
            )
        except jwt.PyJWTError:
            return None

    return None


def get_auth(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> AuthContext | None:
    return resolve_auth(db, request)


def require_auth_ctx(auth: AuthContext | None) -> AuthContext:
    if auth is None:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return auth
