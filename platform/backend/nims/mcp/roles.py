"""Map ApiTokenRole to MCP tool metadata (minRole) and filter tool lists / calls consistently."""

from __future__ import annotations

from typing import Any

from nims.models_generated import Apitokenrole

_IC_KEY = "intentcenter"

# READ < WRITE < ADMIN
_ROLE_ORDER: dict[Apitokenrole, int] = {
    Apitokenrole.READ: 0,
    Apitokenrole.WRITE: 1,
    Apitokenrole.ADMIN: 2,
}


def parse_min_role(meta: dict[str, Any] | None) -> Apitokenrole:
    """Default: READ (same as the current copilot read/preview tool set)."""
    if not meta:
        return Apitokenrole.READ
    block = meta.get(_IC_KEY) if isinstance(meta, dict) else None
    if not isinstance(block, dict):
        return Apitokenrole.READ
    raw = block.get("minRole") or block.get("min_role") or "READ"
    s = str(raw).strip().upper()
    if s not in ("READ", "WRITE", "ADMIN"):
        return Apitokenrole.READ
    return Apitokenrole[s]


def role_satisfies(actor: Apitokenrole, required: Apitokenrole) -> bool:
    return _ROLE_ORDER[actor] >= _ROLE_ORDER[required]
