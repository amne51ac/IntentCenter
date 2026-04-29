import datetime
import re
from enum import Enum

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from nims.config import get_settings
from nims.db import get_db
from nims.models_generated import User

router = APIRouter(tags=["auth"])


class LoginBody(BaseModel):
    email: str = Field(min_length=3)
    password: str = Field(min_length=1)


def _session_cookie_secure(request: Request) -> bool:
    """Set Secure only when the client used HTTPS (or a proxy forwarded https)."""
    forwarded = request.headers.get("x-forwarded-proto")
    if forwarded:
        return forwarded.split(",")[0].strip().lower() == "https"
    return request.url.scheme == "https"


def _jwt_expires_delta(s: str) -> datetime.timedelta:
    s = s.strip()
    m = re.match(r"^(\d+)h$", s, re.I)
    if m:
        return datetime.timedelta(hours=int(m.group(1)))
    return datetime.timedelta(hours=12)


def _role_to_str(role: object) -> str:
    """ORM may return a Python enum or, in edge cases, a raw string from the driver."""
    if isinstance(role, Enum):
        return str(role.value)
    return str(role)


def auth_provider_catalog() -> dict[str, list[dict[str, object]]]:
    import os

    providers: list[dict[str, object]] = [
        {"id": "local", "label": "Email & password", "kind": "password", "enabled": True}
    ]
    if os.environ.get("AUTH_LDAP_URL"):
        providers.append(
            {
                "id": "ldap",
                "label": "LDAP / Active Directory",
                "kind": "ldap",
                "enabled": False,
                "note": "Configure worker; bind flow not enabled in this build.",
            }
        )
    else:
        providers.append(
            {
                "id": "ldap",
                "label": "LDAP / Active Directory",
                "kind": "ldap",
                "enabled": False,
                "note": "Set AUTH_LDAP_URL and deploy LDAP bridge (Phase 2).",
            }
        )
    if os.environ.get("AUTH_AZURE_TENANT_ID") and os.environ.get("AUTH_AZURE_CLIENT_ID"):
        providers.append(
            {
                "id": "azure_ad",
                "label": "Microsoft Entra ID (Azure AD)",
                "kind": "azure_ad",
                "enabled": False,
                "note": "OIDC routes wired; complete consent and callback (Phase 2).",
            }
        )
    else:
        providers.append(
            {
                "id": "azure_ad",
                "label": "Microsoft Entra ID (Azure AD)",
                "kind": "azure_ad",
                "enabled": False,
                "note": "Set AUTH_AZURE_TENANT_ID and AUTH_AZURE_CLIENT_ID.",
            }
        )
    if os.environ.get("AUTH_OIDC_ISSUER") and os.environ.get("AUTH_OIDC_CLIENT_ID"):
        providers.append(
            {
                "id": "oidc",
                "label": "OpenID Connect",
                "kind": "oidc",
                "enabled": False,
                "note": "Authorization server discovery pending (Phase 2).",
            }
        )
    else:
        providers.append(
            {
                "id": "oidc",
                "label": "OpenID Connect (generic)",
                "kind": "oidc",
                "enabled": False,
                "note": "Set AUTH_OIDC_ISSUER and AUTH_OIDC_CLIENT_ID.",
            }
        )
    return {"providers": providers}


@router.get("/auth/providers")
def get_providers() -> dict[str, list[dict[str, object]]]:
    return auth_provider_catalog()


@router.post("/auth/login")
def post_login(
    body: LoginBody,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    settings = get_settings()
    email = body.email.strip().lower()
    user = db.execute(
        select(User).where(func.lower(User.email) == email).options(joinedload(User.Organization_))
    ).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    stored_hash = (user.passwordHash or "").strip()
    if not stored_hash:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    try:
        ok = bcrypt.checkpw(body.password.encode("utf-8"), stored_hash.encode("utf-8"))
    except ValueError:
        ok = False
    if not ok:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    org = user.Organization_
    if org is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User record is missing an organization; re-run database seed or fix data.",
        )
    if org.deletedAt is not None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organization inactive")

    from nims.timeutil import utc_now

    delta = _jwt_expires_delta(settings.jwt_expires_in)
    # Integer `exp` avoids driver/ORM + PyJWT edge cases with datetime payloads in some deployments.
    exp_ts = int((utc_now() + delta).timestamp())
    try:
        token = jwt.encode(
            {"sub": str(user.id), "exp": exp_ts},
            settings.jwt_secret,
            algorithm="HS256",
        )
    except (TypeError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Session signing failed (check JWT_SECRET).",
        ) from e

    max_age = int(_jwt_expires_delta(settings.jwt_expires_in).total_seconds())
    response.set_cookie(
        "nims_session",
        token,
        path="/",
        httponly=True,
        secure=_session_cookie_secure(request),
        samesite="lax",
        max_age=max_age,
    )

    return {
        "ok": True,
        "user": {
            "id": str(user.id),
            "email": user.email,
            "displayName": user.displayName,
            "role": _role_to_str(user.role),
            "organization": {
                "id": str(org.id),
                "name": org.name,
                "slug": org.slug,
            },
        },
    }


@router.post("/auth/logout")
def post_logout(request: Request, response: Response) -> dict[str, bool]:
    response.delete_cookie("nims_session", path="/", secure=_session_cookie_secure(request))
    return {"ok": True}


@router.get("/auth/sso/{provider}/start")
def sso_start(provider: str) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content={
            "error": "Not implemented",
            "message": f'SSO start for "{provider}" will redirect to the IdP after Phase 2 wiring.',
        },
    )
