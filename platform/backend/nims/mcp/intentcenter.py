"""FastMCP subclass: role-filtered tools/list and enforcement on tools/call."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any

from mcp.server.fastmcp.exceptions import ToolError
from mcp.server.fastmcp.server import FastMCP
from mcp.types import ContentBlock
from mcp.types import Tool as MCPTool

from nims.mcp.roles import parse_min_role, role_satisfies
from nims.mcp.state import mcp_request_state

logger = logging.getLogger(__name__)


class IntentCenterFastMCP(FastMCP):
    """Filters advertised tools by ApiTokenRole metadata; rejects unauthorized tool calls."""

    async def list_tools(self) -> list[MCPTool]:
        st = mcp_request_state.get()
        if st is None:
            logger.warning("mcp list_tools without request state")
            return []
        actor = st.auth.role
        out: list[MCPTool] = []
        for info in self._tool_manager.list_tools():
            need = parse_min_role(info.meta)
            if not role_satisfies(actor, need):
                continue
            out.append(
                MCPTool(
                    name=info.name,
                    title=info.title,
                    description=info.description,
                    inputSchema=info.parameters,
                    outputSchema=info.output_schema,
                    annotations=info.annotations,
                    icons=info.icons,
                    _meta=info.meta,
                )
            )
        return out

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Sequence[ContentBlock] | dict[str, Any]:
        st = mcp_request_state.get()
        if st is None:
            raise ToolError("MCP request state missing")
        tool = self._tool_manager.get_tool(name)
        if tool is None:
            raise ToolError(f"Unknown tool: {name}")
        need = parse_min_role(tool.meta)
        if not role_satisfies(st.auth.role, need):
            raise ToolError(f"Forbidden: tool {name!r} requires role {need.value} or higher")
        actor = (
            f"token:{st.auth.api_token.id}"
            if st.auth.api_token
            else (f"user:{st.auth.user.id}" if st.auth.user else "unknown")
        )
        logger.info("mcp_tool name=%s org=%s actor=%s", name, st.auth.organization.id, actor)
        return await super().call_tool(name, arguments)
