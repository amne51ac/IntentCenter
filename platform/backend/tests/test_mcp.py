"""MCP: role helpers, tool registration, and auth ASGI 401 for missing credentials."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from nims.mcp.asgi import McpAuthASGI
from nims.mcp.intentcenter import IntentCenterFastMCP
from nims.mcp.register_tools import register_copilot_mcp_tools
from nims.mcp.roles import parse_min_role, role_satisfies
from nims.mcp.state import McpRequestState, mcp_request_state
from nims.models_generated import Apitokenrole


def test_parse_min_role_defaults_read() -> None:
    assert parse_min_role({}) is Apitokenrole.READ
    assert parse_min_role({"intentcenter": {}}) is Apitokenrole.READ
    assert parse_min_role({"intentcenter": {"minRole": "WRITE"}}) is Apitokenrole.WRITE
    assert parse_min_role({"intentcenter": {"minRole": "ADMIN"}}) is Apitokenrole.ADMIN


def test_role_satisfies_hierarchy() -> None:
    assert role_satisfies(Apitokenrole.ADMIN, Apitokenrole.READ)
    assert role_satisfies(Apitokenrole.WRITE, Apitokenrole.READ)
    assert not role_satisfies(Apitokenrole.READ, Apitokenrole.WRITE)


def test_mcp_copilot_tools_register_count() -> None:
    m = IntentCenterFastMCP(
        "test",
        stateless_http=True,
        json_response=True,
        transport_security=None,
        streamable_http_path="/",
        mount_path="/",
    )
    register_copilot_mcp_tools(m)
    names = {t.name for t in m._tool_manager.list_tools()}
    assert "intentcenter.search" in names
    assert "intentcenter.propose_change_preview" in names
    assert len(names) == 8


def test_mcp_list_tools_with_request_state() -> None:
    m = IntentCenterFastMCP(
        "test",
        stateless_http=True,
        json_response=True,
        transport_security=None,
        streamable_http_path="/",
        mount_path="/",
    )
    register_copilot_mcp_tools(m)
    st = mcp_request_state.set(
        McpRequestState(
            db=MagicMock(),
            auth=MagicMock(
                role=Apitokenrole.READ,
                organization=MagicMock(id=1),
                api_token=None,
                user=MagicMock(id=1),
            ),
        )
    )
    try:
        out = asyncio.run(m.list_tools())
        assert len(out) == 8
    finally:
        mcp_request_state.reset(st)


def test_mcp_auth_asgi_unauthorized(monkeypatch) -> None:
    def _no_auth(_db, _req):
        return None

    monkeypatch.setattr("nims.mcp.asgi.resolve_auth", _no_auth)
    sm = MagicMock()
    app = FastAPI()
    async def _inner_should_not_run(_scope, _receive, _send) -> None:  # pragma: no cover
        raise AssertionError("inner should not run without auth")

    app.mount("/mcp", McpAuthASGI(_inner_should_not_run, sm))
    c = TestClient(app, raise_server_exceptions=True)
    r = c.get("/mcp")
    assert r.status_code == 401
    assert r.json() == {"detail": "Unauthorized"}
