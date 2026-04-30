"""Read-only tool execution for the in-app AI assistant (search, stats, resource view, resource graph).

External MCP clients (``/mcp``) call the same :func:`execute_copilot_tool` path via ``nims.mcp.adapters``.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from nims.auth_context import AuthContext
from nims.models_generated import Circuit, Device, IpAddress, Location, Prefix, Provider, Rack, Vrf
from nims.services.copilot_aggregates import device_breakdown_json, location_hierarchy_json
from nims.services.copilot_catalog_list import CATALOG_LIST_QUERY_SPECS, catalog_list_json
from nims.services.copilot_catalog_query import CATALOG_QUERY_SPECS, catalog_query_json
from nims.services.device_hardware import build_device_hardware_tree
from nims.services.global_search import global_search_items
from nims.services.llm_metrics import bump as _metrics_bump
from nims.services.resource_item import load_resource_item
from nims.services.resource_relationships import build_relationship_graph

_MAX_TOOL_CHARS = 50_000

# Models included in org-wide count summaries (kept in sync with global search object families).
_INVENTORY_COUNT_MODELS: dict[str, type] = {
    "Device": Device,
    "Location": Location,
    "Rack": Rack,
    "Vrf": Vrf,
    "Prefix": Prefix,
    "IpAddress": IpAddress,
    "Provider": Provider,
    "Circuit": Circuit,
}


def _count_in_org(db: Session, organization_id: uuid.UUID, model: type) -> int:
    n = db.execute(
        select(func.count())
        .select_from(model)
        .where(
            and_(
                model.organizationId == organization_id,  # type: ignore[attr-defined]
                model.deletedAt.is_(None),  # type: ignore[attr-defined]
            )
        )
    ).scalar_one()
    return int(n or 0)


def _normalize_inventory_type(raw: str | None) -> str | None:
    if raw is None or not str(raw).strip():
        return None
    t = str(raw).strip()
    if t in _INVENTORY_COUNT_MODELS:
        return t
    tl = t.lower()
    alias: dict[str, str] = {
        "device": "Device",
        "devices": "Device",
        "location": "Location",
        "locations": "Location",
        "rack": "Rack",
        "racks": "Rack",
        "vrf": "Vrf",
        "vrfs": "Vrf",
        "prefix": "Prefix",
        "prefixes": "Prefix",
        "ipaddress": "IpAddress",
        "ip": "IpAddress",
        "ips": "IpAddress",
        "ip_address": "IpAddress",
        "ipaddresses": "IpAddress",
        "provider": "Provider",
        "providers": "Provider",
        "circuit": "Circuit",
        "circuits": "Circuit",
    }
    return alias.get(tl)

OPENAI_TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search",
            "description": (
                "Substring search over non-secret columns of inventory objects the user can access (same scope as the "
                "catalog). Excludes credentials, tokens, and similar fields. Not a full catalog of all items of a type; "
                "for org-wide counts use inventory_stats."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "q": {"type": "string", "description": "Search string (matched against accessible object fields)"},
                    "limit": {"type": "integer", "description": "Max results (1-25)", "default": 10},
                },
                "required": ["q"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "inventory_stats",
            "description": (
                "Organization-wide counts of inventory objects (non-deleted). Use for questions like "
                "how many devices, locations, or circuits; do not use search for counts. "
                "Omit resource_type to get a summary; set resource_type to count one type (Device, Location, Rack, Vrf, Prefix, IpAddress, Provider, Circuit)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "resource_type": {
                        "type": "string",
                        "description": "Optional. One of: Device, Location, Rack, Vrf, Prefix, IpAddress, Provider, Circuit. Omit to return all counts.",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_resource_view",
            "description": "Load a single object with fields and relationship graph (same as the object page).",
            "parameters": {
                "type": "object",
                "properties": {
                    "resource_type": {"type": "string", "description": "e.g. Device, Location, Circuit"},
                    "resource_id": {"type": "string", "description": "UUID of the object"},
                },
                "required": ["resource_type", "resource_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_resource_graph",
            "description": "Get only the relationship graph for an object (dependencies and links).",
            "parameters": {
                "type": "object",
                "properties": {
                    "resource_type": {"type": "string"},
                    "resource_id": {"type": "string"},
                },
                "required": ["resource_type", "resource_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_location_hierarchy",
            "description": (
                "List **all** non-deleted locations: id, name, parentId, slug, and when stored in DCIM, **latitude and "
                "longitude** (WGS84) plus hasCoordinates. Use for an indented tree, or for a geographic **map** in "
                "the chat (Markdown `map` code fence with center + markers) when some rows have coordinates. "
                "Read-only; does not return devices."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "device_count_breakdown",
            "description": (
                "**Legacy alias** for grouped counts: same data as `catalog_breakdown` using a `group_by` string instead of "
                "`query`. Prefer `catalog_breakdown` for new questions so you can pick any `Entity/dimension` id from the "
                "composable list (devices, circuits, racks by location, status, provider, etc.)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "group_by": {
                        "type": "string",
                        "enum": [
                            "location",
                            "device_type",
                            "device_role",
                            "status",
                            "circuits_by_location",
                        ],
                        "description": (
                            "location: count devices at each site (devices in racks; unplaced in 'Unplaced'). "
                            "device_type: per hardware type. device_role: per role name. status: per lifecycle status. "
                            "circuits_by_location: count distinct circuits that have a termination at each site "
                            "(a circuit touching two sites appears in both rows)."
                        ),
                    }
                },
                "required": ["group_by"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "catalog_breakdown",
            "description": (
                "**Composable aggregates (read-only):** org-scoped **grouped counts** by a validated `query` id "
                "(`BaseEntity/dimension`, e.g. `Device/location`, `Circuit/provider`). For **row-level lists** of "
                "entities matching a filter, use `catalog_list` (same id style, different tool). Use for tables, "
                "`chart` blocks, and **multi-step** analysis. Server runs SQL. New patterns extend the enum; you do not "
                "wait for a new top-level tool name for every report type that fits the same pattern."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "enum": CATALOG_QUERY_SPECS,
                        "description": "Composite id: which objects to count and by which dimension (see enum).",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "catalog_list",
            "description": (
                "**Composable row lists** (read-only): return up to `limit` **rows** for a validated `query` id, e.g. "
                "`Device/without_interfaces` = devices with no non-deleted `Interface` records. Use for Markdown tables "
                "and audits. Check `totalCount` and `truncated`. Pair with `catalog_breakdown` and `inventory_stats` in "
                "multi-step answers. New list types are new **enum values**, not new tool names."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "enum": CATALOG_LIST_QUERY_SPECS,
                        "description": "List id: which entities and which filter (see enum).",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max rows (1–200). Default 100.",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "propose_change_preview",
            "description": (
                "Propose a batch of intended **writes** for **human review only**. Does **not** modify any data. "
                "Call this when the user wants to plan updates, creates, or archive actions. "
                "The response includes current object snapshots and your proposed `field_deltas` for each change, "
                "if you supplied a `resource_id` the user can see what would be affected."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "One-paragraph description of the overall plan.",
                    },
                    "changes": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "action": {
                                    "type": "string",
                                    "enum": ["update", "create", "archive"],
                                },
                                "resource_type": {"type": "string", "description": "e.g. Device, Location"},
                                "resource_id": {
                                    "type": "string",
                                    "description": "UUID of the object, when applicable; omit for purely conceptual create.",
                                },
                                "rationale": {"type": "string", "description": "Why this change (short)."},
                                "field_deltas": {
                                    "type": "object",
                                    "description": "Suggested field names → proposed values (read-only preview).",
                                },
                            },
                            "required": ["action", "resource_type", "rationale"],
                        },
                    },
                },
                "required": ["summary", "changes"],
            },
        },
    },
]


def _clip(s: str) -> str:
    if len(s) <= _MAX_TOOL_CHARS:
        return s
    return s[: _MAX_TOOL_CHARS - 80] + "\n... [truncated for size]"


def execute_copilot_tool(
    db: Session,
    ctx: AuthContext,
    name: str,
    arguments: dict[str, Any] | str | None,
) -> str:
    _metrics_bump("copilotToolCalls", 1)
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments) if arguments.strip() else {}
        except (json.JSONDecodeError, TypeError, AttributeError):
            arguments = {}
    if not isinstance(arguments, dict):
        arguments = {}
    oid = ctx.organization.id

    if name == "inventory_stats":
        rraw = arguments.get("resource_type")
        rs = str(rraw).strip() if rraw is not None and str(rraw).strip() else None
        rt = _normalize_inventory_type(rs) if rs else None
        if rs and rt is None:
            return json.dumps(
                {
                    "error": f"Unknown resource_type: {rs!r}",
                    "allowed": sorted(_INVENTORY_COUNT_MODELS.keys()),
                }
            )
        if rt is not None:
            m = _INVENTORY_COUNT_MODELS[rt]
            c = _count_in_org(db, oid, m)
            return json.dumps(
                {
                    "resourceType": rt,
                    "count": c,
                    "note": "Non-deleted objects in the current organization.",
                }
            )
        row = {k: _count_in_org(db, oid, m) for k, m in _INVENTORY_COUNT_MODELS.items()}
        row["total"] = sum(row.values())
        return json.dumps(
            {
                "counts": row,
                "note": "Non-deleted objects in the current organization. Keys are resource types (PascalCase).",
            }
        )

    if name == "search":
        q = str(arguments.get("q", ""))
        try:
            limit = int(arguments.get("limit", 10))
        except (TypeError, ValueError):
            limit = 10
        limit = max(1, min(limit, 25))
        items = global_search_items(db, oid, q, limit)
        return _clip(json.dumps({"items": items}))

    if name in ("get_resource_view", "get_resource_graph"):
        rt = str(arguments.get("resource_type", "")).strip()
        if rt == "Service":
            rt = "ServiceInstance"
        try:
            rid = uuid.UUID(str(arguments.get("resource_id", "")))
        except (ValueError, TypeError):
            return json.dumps({"error": "invalid resource_id (expected UUID)"})

    if name == "get_resource_view":
        item = load_resource_item(db, oid, rt, rid)
        graph = build_relationship_graph(db, oid, rt, rid)
        if item is None and graph is None:
            return json.dumps({"error": "Object not found"})
        if item is None and graph is not None:
            root = graph.get("root") or {}
            item = {"id": root.get("id"), "label": root.get("label"), "meta": root.get("meta")}

        hardware = None
        if rt == "Device" and item is not None:
            hardware = build_device_hardware_tree(db, oid, rid)
        return _clip(
            json.dumps(
                {
                    "resourceType": rt,
                    "item": item,
                    "graph": graph,
                    "hardware": hardware,
                },
                default=str,
            )
        )

    if name == "get_resource_graph":
        g = build_relationship_graph(db, oid, rt, rid)
        if g is None:
            return json.dumps({"error": "Object not found or graph not available"})
        return _clip(json.dumps(g, default=str))

    if name == "list_location_hierarchy":
        return _clip(location_hierarchy_json(db, oid))

    if name == "device_count_breakdown":
        gb = str(arguments.get("group_by", "") or "").strip()
        if not gb:
            return json.dumps(
                {
                    "error": "group_by is required",
                    "enum": [
                        "location",
                        "device_type",
                        "device_role",
                        "status",
                        "circuits_by_location",
                    ],
                }
            )
        return _clip(device_breakdown_json(db, oid, gb))

    if name == "catalog_breakdown":
        q = str(arguments.get("query", "") or "").strip()
        if not q:
            return json.dumps(
                {
                    "error": "query is required",
                    "allowedQueries": CATALOG_QUERY_SPECS,
                }
            )
        return _clip(catalog_query_json(db, oid, q))

    if name == "catalog_list":
        q = str(arguments.get("query", "") or "").strip()
        if not q:
            return json.dumps(
                {
                    "error": "query is required",
                    "allowedQueries": CATALOG_LIST_QUERY_SPECS,
                }
            )
        try:
            lim = int(arguments.get("limit", 100))
        except (TypeError, ValueError):
            lim = 100
        return _clip(catalog_list_json(db, oid, q, lim))

    if name == "propose_change_preview":
        summary = str(arguments.get("summary", ""))[:4000]
        ch_raw = arguments.get("changes")
        if not isinstance(ch_raw, list):
            ch_raw = []
        previews: list[dict[str, Any]] = []
        for ch in ch_raw:
            if not isinstance(ch, dict):
                continue
            action = str(ch.get("action", "update") or "update").lower()
            rtype = str(ch.get("resource_type", "") or "").strip()
            if rtype == "Service":
                rtype = "ServiceInstance"
            rationale = str(ch.get("rationale", ""))[:4000]
            fd = ch.get("field_deltas")
            if not isinstance(fd, dict):
                fd = {}
            rid_s = ch.get("resource_id")
            if not rid_s:
                previews.append(
                    {
                        "action": action,
                        "resourceType": rtype,
                        "rationale": rationale,
                        "fieldDeltasProposed": fd,
                        "readOnly": True,
                        "note": "No resource_id — planning-only until an id is available.",
                    }
                )
                continue
            try:
                rid2 = uuid.UUID(str(rid_s).strip())
            except (ValueError, TypeError):
                previews.append(
                    {
                        "action": action,
                        "resourceType": rtype,
                        "rationale": rationale,
                        "error": "invalid resource_id (expected UUID)",
                    }
                )
                continue
            if not rtype:
                previews.append({"error": "resource_type required with resource_id", "resourceId": str(rid2)})
                continue
            current = load_resource_item(db, oid, rtype, rid2)
            if current is None:
                previews.append(
                    {
                        "action": action,
                        "resourceType": rtype,
                        "resourceId": str(rid2),
                        "rationale": rationale,
                        "fieldDeltasProposed": fd,
                        "readOnly": True,
                        "notFound": True,
                    }
                )
            else:
                previews.append(
                    {
                        "action": action,
                        "resourceType": rtype,
                        "resourceId": str(rid2),
                        "rationale": rationale,
                        "fieldDeltasProposed": fd,
                        "currentSnapshot": current,
                        "readOnly": True,
                    }
                )
        return _clip(
            json.dumps(
                {
                    "summary": summary,
                    "previews": previews,
                    "readOnly": True,
                    "disclaimer": "Preview only. No inventory or configuration was written.",
                },
                default=str,
            )
        )

    return json.dumps({"error": f"unknown tool {name}"})


def build_context_block(context: dict[str, Any] | None) -> str:
    if not context:
        return ""
    parts: list[str] = []
    r = (context.get("route") or context.get("path") or "").strip()
    rt = (context.get("resourceType") or context.get("resource_type") or "").strip()
    rid = (context.get("id") or context.get("resourceId") or "").strip()
    label = (context.get("label") or "").strip()
    if r:
        parts.append(f"Current app route: {r}")
    if rt or rid:
        parts.append(f"Focused object: type={rt or 'unknown'} id={rid or 'n/a'}" + (f" label={label}" if label else ""))
    if not parts:
        return ""
    return "\n".join(parts) + "\n\n"
