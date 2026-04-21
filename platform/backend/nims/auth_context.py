from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from fastapi import HTTPException, status

if TYPE_CHECKING:
    from nims.models_generated import ApiToken, Organization


@dataclass
class UserAuth:
    id: str
    email: str
    displayName: str | None
    authProvider: str


@dataclass
class AuthContext:
    organization: "Organization"
    role: object  # Apitokenrole enum
    api_token: Optional["ApiToken"] = None
    user: UserAuth | None = None


def auth_actor_from_context(ctx: AuthContext) -> str:
    if ctx.user:
        return f"user:{ctx.user.id}"
    if ctx.api_token:
        return f"token:{ctx.api_token.id}"
    return "unknown"


def require_write(ctx: AuthContext | None) -> AuthContext:
    if not ctx:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    from nims.models_generated import Apitokenrole

    if ctx.role == Apitokenrole.READ:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: read-only")
    return ctx


def require_admin(ctx: AuthContext | None) -> AuthContext:
    if not ctx:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    from nims.models_generated import Apitokenrole

    if ctx.role != Apitokenrole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: admin required")
    return ctx
