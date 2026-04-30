"""Register MCP tools backed by copilot_tools (shared execution, role metadata on each tool)."""

from __future__ import annotations

from typing import Any

from nims.mcp import adapters
from nims.mcp.intentcenter import IntentCenterFastMCP
from nims.services.copilot_tools import OPENAI_TOOL_DEFINITIONS

_READ_META: dict[str, Any] = {"intentcenter": {"minRole": "READ", "source": "copilot_tools"}}

# OpenAI function name -> (mcp tool name, adapter callable on nims.mcp.adapters)
_TOOL_MAP: list[tuple[str, str, Any]] = [
    ("search", "intentcenter.search", adapters.intentcenter_search),
    ("inventory_stats", "intentcenter.inventory_stats", adapters.intentcenter_inventory_stats),
    ("get_resource_view", "intentcenter.get_resource_view", adapters.intentcenter_get_resource_view),
    ("get_resource_graph", "intentcenter.get_resource_graph", adapters.intentcenter_get_resource_graph),
    ("list_location_hierarchy", "intentcenter.list_location_hierarchy", adapters.intentcenter_list_location_hierarchy),
    ("device_count_breakdown", "intentcenter.device_count_breakdown", adapters.intentcenter_device_count_breakdown),
    ("catalog_breakdown", "intentcenter.catalog_breakdown", adapters.intentcenter_catalog_breakdown),
    ("propose_change_preview", "intentcenter.propose_change_preview", adapters.intentcenter_propose_change_preview),
]


def _descriptions_by_copilot_name() -> dict[str, str]:
    out: dict[str, str] = {}
    for entry in OPENAI_TOOL_DEFINITIONS:
        fn = entry.get("function")
        if not isinstance(fn, dict):
            continue
        n = fn.get("name")
        d = fn.get("description")
        if isinstance(n, str) and isinstance(d, str):
            out[n] = d
    return out


def register_copilot_mcp_tools(m: IntentCenterFastMCP) -> None:
    """Wire one MCP tool per OpenAI copilot function; names are namespaced with ``intentcenter.`` prefix."""
    desc = _descriptions_by_copilot_name()
    for copilot_name, mcp_name, fn in _TOOL_MAP:
        description = desc.get(copilot_name) or (fn.__doc__ or "").strip() or f"Copilot tool `{copilot_name}`."
        m.add_tool(fn, name=mcp_name, description=description, meta=dict(_READ_META))
