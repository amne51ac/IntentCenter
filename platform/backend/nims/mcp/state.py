"""Per-request context for MCP (DB session + auth), set by ASGI middleware before the MCP transport runs."""

from __future__ import annotations

import contextvars
from dataclasses import dataclass

from sqlalchemy.orm import Session

from nims.auth_context import AuthContext


@dataclass
class McpRequestState:
    """Holds the same auth and DB session for one HTTP request to /mcp (stateless transport: one shot)."""

    db: Session
    auth: AuthContext


mcp_request_state: contextvars.ContextVar[McpRequestState | None] = contextvars.ContextVar(
    "mcp_request_state",
    default=None,
)
