"""Build Streamable HTTP MCP stack (stateless JSON) for mounting on FastAPI; session manager for lifespan."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from mcp.server.fastmcp.server import StreamableHTTPASGIApp

from nims.mcp.asgi import McpAuthASGI
from nims.mcp.intentcenter import IntentCenterFastMCP
from nims.mcp.register_tools import register_copilot_mcp_tools

if TYPE_CHECKING:
    from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

logger = logging.getLogger(__name__)


def build_mcp_stack() -> tuple[StreamableHTTPSessionManager, McpAuthASGI]:
    """
    Create the MCP server, register copilot-backed tools, and return the session manager + authenticated ASGI app.

    Call :meth:`StreamableHTTPSessionManager.run` from the FastAPI lifespan. Do not use the Starlette app
    returned by :meth:`IntentCenterFastMCP.streamable_http_app` directly (it would duplicate lifespan / not
    wrap auth).
    """
    mcp = IntentCenterFastMCP(
        "IntentCenter",
        instructions=(
            "IntentCenter inventory and DCIM. Tools read org-scoped data and mirror the in-app copilot "
            "(search, stats, resource view, previews). Use the same API token you use for REST: "
            "Authorization: Bearer <token>."
        ),
        stateless_http=True,
        json_response=True,
        streamable_http_path="/",
        mount_path="/",
        transport_security=None,
    )
    register_copilot_mcp_tools(mcp)
    # Side effect: initializes StreamableHTTPSessionManager used by streamable_http_app
    mcp.streamable_http_app()
    sm = mcp.session_manager
    core = StreamableHTTPASGIApp(sm)
    logger.info("MCP streamable HTTP enabled (stateless, JSON), tools=copilot bridge")
    return sm, McpAuthASGI(core, sm)
