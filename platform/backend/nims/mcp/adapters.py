"""Thin MCP tool callables: delegate to copilot_tools.execute_copilot_tool (same behavior as in-app assistant)."""

from __future__ import annotations

import json
from typing import Any

from nims.mcp.state import mcp_request_state
from nims.services.copilot_tools import execute_copilot_tool


def _run(name: str, arguments: dict[str, Any]) -> str:
    st = mcp_request_state.get()
    if st is None:
        return json.dumps({"error": "MCP request state missing (auth middleware not applied?)"})
    return execute_copilot_tool(st.db, st.auth, name, arguments)


def intentcenter_search(q: str, limit: int = 10) -> str:
    """Substring search over org-visible inventory (same as copilot `search`)."""
    return _run("search", {"q": q, "limit": limit})


def intentcenter_inventory_stats(resource_type: str | None = None) -> str:
    """Org-wide object counts; optional `resource_type` to count one kind."""
    args: dict[str, Any] = {}
    if resource_type is not None and str(resource_type).strip():
        args["resource_type"] = resource_type
    return _run("inventory_stats", args)


def intentcenter_get_resource_view(resource_type: str, resource_id: str) -> str:
    """Load one object with graph (same as object view page)."""
    return _run("get_resource_view", {"resource_type": resource_type, "resource_id": resource_id})


def intentcenter_get_resource_graph(resource_type: str, resource_id: str) -> str:
    """Relationship graph only for an object."""
    return _run("get_resource_graph", {"resource_type": resource_type, "resource_id": resource_id})


def intentcenter_list_location_hierarchy() -> str:
    """All locations in the org (tree + coordinates when present)."""
    return _run("list_location_hierarchy", {})


def intentcenter_device_count_breakdown(group_by: str) -> str:
    """Legacy grouped device/circuit counts by dimension string."""
    return _run("device_count_breakdown", {"group_by": group_by})


def intentcenter_catalog_breakdown(query: str) -> str:
    """Composable org-scoped SQL aggregates (query id = Entity/dimension)."""
    return _run("catalog_breakdown", {"query": query})


def intentcenter_propose_change_preview(summary: str, changes: list) -> str:
    """Read-only change preview; does not mutate data (same as copilot)."""
    return _run("propose_change_preview", {"summary": summary, "changes": changes})
