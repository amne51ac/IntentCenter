"""ASGI wrapper: resolve REST-style auth, set MCP request state, forward to Streamable HTTP transport."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import Receive, Scope, Send

from nims.db import SessionLocal
from nims.deps import resolve_auth
from nims.mcp.state import McpRequestState, mcp_request_state

if TYPE_CHECKING:  # pragma: no cover
    from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

logger = logging.getLogger(__name__)


class McpAuthASGI:
    """Outer ASGI: ``Authorization: Bearer`` (or session cookie) → :func:`resolve_auth`; 401 if unauthenticated."""

    def __init__(self, inner: Callable[[Scope, Receive, Send], object], _session_manager: StreamableHTTPSessionManager):
        self.inner = inner
        # Retain ref for API symmetry / future (e.g. health); transport does not use it on the wrapper.
        self._session_manager = _session_manager

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.inner(scope, receive, send)
            return

        request = Request(scope, receive)
        db = SessionLocal()
        token = None
        try:
            ctx = resolve_auth(db, request)
            if ctx is None:
                await JSONResponse(
                    {"detail": "Unauthorized"},
                    status_code=401,
                    headers={"WWW-Authenticate": "Bearer"},
                )(scope, receive, send)
                return
            st = McpRequestState(db=db, auth=ctx)
            token = mcp_request_state.set(st)
            if ctx.api_token:
                who = f"token:{ctx.api_token.id}"
            else:
                who = f"user:{ctx.user.id if ctx.user else '?'}"  # pragma: no cover
            logger.debug("mcp request actor=%s org=%s", who, ctx.organization.id)
            await self.inner(scope, receive, send)
        finally:
            if token is not None:
                mcp_request_state.reset(token)
            db.close()
