"""IntentCenter Copilot: LLM chat, skills, admin LLM settings, suggestions."""

from __future__ import annotations

import json
import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from nims.auth_context import AuthContext, auth_actor_from_context, require_admin
from nims.deps import get_auth, get_db, require_auth_ctx
from nims.models_generated import Apitokenrole, CopilotSkill, Copilotskillvisibility, Organization
from nims.services.audit import record_audit
from nims.services.llm_config import (
    apply_admin_llm_patch,
    build_admin_llm_response,
    get_effective_llm_for_runtime,
    resolve_llm_for_connection_test,
)
from nims.services.llm_metrics import bump, snapshot
from nims.services.llm_openai import (
    iter_copilot_chat_sse,
    run_copilot_chat,
    run_import_column_mapping,
    run_suggest_next_steps,
    run_suggestion_titles,
    run_suggest_thread_title,
    run_ticket_triage_summary,
)
from nims.services.resource_item import load_resource_item
from nims.services.ticket_triage import build_triage_hits
from nims.services.llm_test import test_openai_chat_minimal
from nims.timeutil import utc_now

router = APIRouter(tags=["copilot"])


def _org(db: Session, ctx: AuthContext) -> Organization:
    o = db.get(Organization, ctx.organization.id)
    if o is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Organization not found")
    return o


# --- Admin LLM ---


@router.get("/admin/llm")
def get_admin_llm(
    db: Session = Depends(get_db),
    auth: AuthContext | None = Depends(get_auth),
) -> dict[str, Any]:
    ctx = require_admin(require_auth_ctx(auth))
    return build_admin_llm_response(_org(db, ctx))


@router.patch("/admin/llm")
def patch_admin_llm(
    body: Annotated[dict[str, Any], Body(...)],
    db: Session = Depends(get_db),
    auth: AuthContext | None = Depends(get_auth),
) -> dict[str, Any]:
    ctx = require_admin(require_auth_ctx(auth))
    org = _org(db, ctx)
    apply_admin_llm_patch(org, body)
    try:
        flag_modified(org, "llmConfig")
    except (AttributeError, TypeError, ValueError):
        pass
    record_audit(
        db,
        organization_id=ctx.organization.id,
        actor=auth_actor_from_context(ctx),
        action="UPDATE",
        resource_type="Organization",
        resource_id=str(org.id),
        after={"field": "llmConfig", "keysTouched": sorted(body.keys())},
    )
    db.commit()
    return build_admin_llm_response(org)


@router.post("/admin/llm/test")
def post_admin_llm_test(
    body: dict[str, Any] | None = Body(default=None),
    db: Session = Depends(get_db),
    auth: AuthContext | None = Depends(get_auth),
) -> dict[str, Any]:
    """Verify OpenAI-compatible /chat/completions with current or draft values (admin only)."""
    ctx = require_admin(require_auth_ctx(auth))
    org = _org(db, ctx)
    creds = resolve_llm_for_connection_test(org, body)
    ok, message = test_openai_chat_minimal(
        creds["baseUrl"],
        creds["apiKey"],
        creds["defaultModel"],
    )
    return {"ok": ok, "message": message}


@router.get("/admin/llm/metrics")
def get_admin_llm_metrics(
    auth: AuthContext | None = Depends(get_auth),
) -> dict[str, Any]:
    """In-process copilot/LLM usage counters (admin only)."""
    require_admin(require_auth_ctx(auth))
    return {"metrics": snapshot()}


# --- Copilot chat ---


@router.post("/copilot/chat")
def post_copilot_chat(
    body: Annotated[dict[str, Any], Body(...)],
    db: Session = Depends(get_db),
    auth: AuthContext | None = Depends(get_auth),
) -> dict[str, Any]:
    ctx = require_auth_ctx(auth)
    org = _org(db, ctx)
    eff = get_effective_llm_for_runtime(org)
    if not eff.get("enabled"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The AI assistant is not enabled. Configure LLM in Admin or set LLM_* environment variables.",
        )
    if not eff.get("baseUrl") or not eff.get("apiKey"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM is not fully configured (base URL and API key required).",
        )
    messages = body.get("messages")
    if not isinstance(messages, list) or not messages:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="messages array required")
    page_context = body.get("context")
    if page_context is not None and not isinstance(page_context, dict):
        page_context = None
    umsgs: list[dict[str, str]] = []
    for m in messages:
        if not isinstance(m, dict):
            continue
        role = m.get("role")
        content = m.get("content")
        if role in ("user", "assistant") and isinstance(content, str):
            umsgs.append({"role": role, "content": content})
    bump("copilotChatRequests", 1)
    text = run_copilot_chat(
        db,
        ctx,
        str(eff["baseUrl"]),
        str(eff["apiKey"]),
        str(eff.get("defaultModel") or "gpt-4.1-mini"),
        umsgs,
        page_context,
    )
    return {"message": {"role": "assistant", "content": text}}


@router.post("/copilot/chat/stream")
def post_copilot_chat_stream(
    body: Annotated[dict[str, Any], Body(...)],
    db: Session = Depends(get_db),
    auth: AuthContext | None = Depends(get_auth),
) -> StreamingResponse:
    """
    Server-sent events: each line is ``data: <json>`` with types ``delta``, ``status``,
    ``error``, and ``done``. Client should accumulate ``delta`` text for the assistant message.
    """
    ctx = require_auth_ctx(auth)
    org = _org(db, ctx)
    eff = get_effective_llm_for_runtime(org)
    if not eff.get("enabled"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The AI assistant is not enabled. Configure LLM in Admin or set LLM_* environment variables.",
        )
    if not eff.get("baseUrl") or not eff.get("apiKey"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM is not fully configured (base URL and API key required).",
        )
    messages = body.get("messages")
    if not isinstance(messages, list) or not messages:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="messages array required")
    page_context = body.get("context")
    if page_context is not None and not isinstance(page_context, dict):
        page_context = None
    umsgs: list[dict[str, str]] = []
    for m in messages:
        if not isinstance(m, dict):
            continue
        role = m.get("role")
        content = m.get("content")
        if role in ("user", "assistant") and isinstance(content, str):
            umsgs.append({"role": role, "content": content})

    bump("copilotStreamSessions", 1)

    def gen():
        for ev in iter_copilot_chat_sse(
            db,
            ctx,
            str(eff["baseUrl"]),
            str(eff["apiKey"]),
            str(eff.get("defaultModel") or "gpt-4.1-mini"),
            umsgs,
            page_context,
        ):
            yield f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"
        # explicit stream end (some clients expect it)
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        gen(),
        media_type="text/event-stream; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/copilot/assist/import-mapping")
def post_copilot_assist_import_mapping(
    body: Annotated[dict[str, Any], Body(...)],
    db: Session = Depends(get_db),
    auth: AuthContext | None = Depends(get_auth),
) -> dict[str, Any]:
    """
    LLM-suggested column mapping for bulk import (read-only: returns JSON only).
    Body: ``targetResourceType`` (e.g. Device), ``columns`` (string[]), ``sampleRows`` (array of row objects, optional).
    """
    ctx = require_auth_ctx(auth)
    org = _org(db, ctx)
    eff = get_effective_llm_for_runtime(org)
    if not eff.get("enabled") or not eff.get("baseUrl") or not eff.get("apiKey"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The AI assistant is not enabled or LLM is not fully configured.",
        )
    t_rt = str(body.get("targetResourceType") or body.get("target_resource_type") or "").strip()
    if not t_rt:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="targetResourceType is required")
    cols_raw = body.get("columns")
    if not isinstance(cols_raw, list) or not cols_raw:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="columns (non-empty array) is required")
    cols: list[str] = [str(c) for c in cols_raw if str(c).strip()]
    srows: list[dict[str, str]] = []
    sr = body.get("sampleRows") or body.get("sample_rows")
    if isinstance(sr, list):
        for row in sr[:20]:
            if not isinstance(row, dict):
                continue
            d: dict[str, str] = {}
            for k, v in list(row.items())[:80]:
                if v is None:
                    continue
                d[str(k)[:200]] = str(v)[:2000]
            srows.append(d)
    bump("importMappingRequests", 1)
    parsed = run_import_column_mapping(
        str(eff["baseUrl"]),
        str(eff["apiKey"]),
        str(eff.get("defaultModel") or "gpt-4.1-mini"),
        t_rt,
        cols,
        srows,
    )
    if not parsed:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not produce an import column mapping. Try different column names or a smaller sample.",
        )
    return {"readOnly": True, "targetResourceType": t_rt, **parsed}


@router.post("/copilot/assist/ticket-triage")
def post_copilot_assist_ticket_triage(
    body: Annotated[dict[str, Any], Body(...)],
    db: Session = Depends(get_db),
    auth: AuthContext | None = Depends(get_auth),
) -> dict[str, Any]:
    """
    Pasted ticket/incident: extract hostnames/IPs, search inventory; optional LLM summary.
    Body: ``text`` (string), ``summarize`` (optional bool, default true if LLM available).
    """
    ctx = require_auth_ctx(auth)
    org = _org(db, ctx)
    pasted = str(body.get("text", "") or "")
    if not pasted.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="text is required")
    do_summary = bool(body.get("summarize", True))
    triage = build_triage_hits(db, ctx.organization.id, pasted)
    bump("ticketTriageRequests", 1)
    eff = get_effective_llm_for_runtime(org)
    summary: str | None = None
    if do_summary and eff.get("enabled") and eff.get("baseUrl") and eff.get("apiKey"):
        summary = run_ticket_triage_summary(
            str(eff["baseUrl"]),
            str(eff["apiKey"]),
            str(eff.get("defaultModel") or "gpt-4.1-mini"),
            pasted,
            triage,
        )
    return {"readOnly": True, **triage, "summary": summary}


@router.post("/copilot/suggest_thread_title")
def post_suggest_thread_title(
    body: Annotated[dict[str, Any], Body(...)],
    db: Session = Depends(get_db),
    auth: AuthContext | None = Depends(get_auth),
) -> dict[str, Any]:
    """
    Suggest a short display title for a chat after the first user+assistant turn.
    Returns { "title": str | null }; null if LLM is unavailable or generation fails.
    """
    ctx = require_auth_ctx(auth)
    org = _org(db, ctx)
    u = str(body.get("userMessage", "") or body.get("user_message", ""))
    a = str(body.get("assistantMessage", "") or body.get("assistant_message", ""))
    if not (u and str(u).strip()):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="userMessage is required")
    eff = get_effective_llm_for_runtime(org)
    if not eff.get("enabled") or not eff.get("baseUrl") or not eff.get("apiKey"):
        return {"title": None}
    title = run_suggest_thread_title(
        str(eff["baseUrl"]),
        str(eff["apiKey"]),
        str(eff.get("defaultModel") or "gpt-4.1-mini"),
        u,
        a,
    )
    return {"title": title}


def _enrich_page_for_next_steps(
    db: Session,
    organization_id: uuid.UUID,
    context: dict[str, Any] | None,
) -> str:
    """Narrow server-side view of the current app page for the LLM."""
    if not context or not isinstance(context, dict):
        return "Client route: (not provided)"
    r = (context.get("route") or context.get("path") or "").strip()
    parts: list[str] = [f"Client route: {r or '/'} (IntentCenter single-page app)"]
    rt = (context.get("resourceType") or context.get("resource_type") or "").strip()
    rid = (context.get("id") or context.get("resourceId") or "").strip()
    if not rt or not rid:
        return "\n".join(parts)
    try:
        uid = uuid.UUID(str(rid))
    except (ValueError, TypeError):
        return "\n".join(parts + [f"Object route: type {rt!r} — id in URL is not a valid UUID."])
    item = load_resource_item(db, organization_id, rt, uid)
    if item is None:
        return "\n".join(parts + [f"Object page: {rt} (id from URL) — not found in inventory."])
    label = str(
        item.get("name")
        or item.get("label")
        or item.get("title")
        or item.get("displayName")
        or item.get("cid")
        or item.get("address")
        or item.get("id", "")
    )[:300]
    parts.append(f"Object shown in the UI: {rt} with primary label: {label!r}.")
    return "\n".join(parts)


def _format_messages_for_next_steps(raw: list[Any]) -> str:
    lines: list[str] = []
    if not isinstance(raw, list):
        return ""
    for m in raw[-40:]:
        if not isinstance(m, dict):
            continue
        role = m.get("role")
        c = m.get("content")
        if role not in ("user", "assistant") or not isinstance(c, str):
            continue
        c2 = c.strip()
        if not c2:
            continue
        lines.append(f"{str(role).upper()}: {c2}")
    t = "\n\n".join(lines)
    if len(t) > 10_000:
        t = t[-10_000:]
    return t


@router.post("/copilot/suggest_next_steps")
def post_suggest_next_steps(
    body: Annotated[dict[str, Any], Body(...)],
    db: Session = Depends(get_db),
    auth: AuthContext | None = Depends(get_auth),
) -> dict[str, Any]:
    """
    LLM-generated 3 “where to go next” chip options: current app page (server-enriched),
    plus recent chat, returned as { suggestions: [ { id, label, prompt } x 3 ] }.
    If LLM is not configured, returns { suggestions: [] }.
    """
    ctx = require_auth_ctx(auth)
    org = _org(db, ctx)
    page_ctx = body.get("context")
    if page_ctx is not None and not isinstance(page_ctx, dict):
        page_ctx = None
    umsgs: list[dict[str, str]] = []
    rawm = body.get("messages")
    if isinstance(rawm, list):
        for m in rawm:
            if not isinstance(m, dict):
                continue
            role = m.get("role")
            c = m.get("content")
            if role in ("user", "assistant") and isinstance(c, str) and c.strip():
                umsgs.append({"role": str(role), "content": c.strip()})
    eff = get_effective_llm_for_runtime(org)
    if not eff.get("enabled") or not eff.get("baseUrl") or not eff.get("apiKey"):
        return {"suggestions": []}
    page_s = _enrich_page_for_next_steps(
        db,
        ctx.organization.id,
        page_ctx if isinstance(page_ctx, dict) else None,
    )
    chat_t = _format_messages_for_next_steps(umsgs)
    out = run_suggest_next_steps(
        str(eff["baseUrl"]),
        str(eff["apiKey"]),
        str(eff.get("defaultModel") or "gpt-4.1-mini"),
        page_s,
        chat_t,
    )
    return {"suggestions": out}


# --- Suggestions (chips) ---


def _static_chips(resource_type: str | None, route: str) -> list[dict[str, Any]]:
    """Deterministic first steps; no LLM required."""
    rt = (resource_type or "").strip()
    out: list[dict[str, Any]] = [
        {
            "id": "search_hint",
            "label": "Search by name, IP, or CIDR",
            "prompt": "I want to find specific objects. Help me pick a good search string (a hostname fragment, IP, or prefix) and use the search tool; remind me that search does not return full catalog lists.",
        }
    ]
    if rt:
        out.insert(
            0,
            {
                "id": "graph_summary",
                "label": f"Summarize links for this {rt}",
                "prompt": f"The user is focused on a {rt} in the app. Use get_resource_view or get_resource_graph to summarize relationships and what depends on it. Current route: {route or 'unknown'}.",  # noqa: E501
            },
        )
    else:
        out.insert(
            0,
            {
                "id": "overview",
                "label": "What can I do in IntentCenter?",
                "prompt": "Briefly explain what inventory object types we track. Say that I can get counts with the inventory_stats tool, search by name/IP with the search tool, and open a specific object with get_resource_view when I have a type and id.",
            },
        )
    return out[:5]


@router.get("/copilot/suggestions")
def get_copilot_suggestions(
    resourceType: str | None = Query(None, alias="resourceType"),
    route: str = Query(""),
    db: Session = Depends(get_db),
    auth: AuthContext | None = Depends(get_auth),
) -> dict[str, Any]:
    ctx = require_auth_ctx(auth)
    org = _org(db, ctx)
    eff = get_effective_llm_for_runtime(org)
    chips = _static_chips(resourceType, route)
    if ctx.user:
        qspec = or_(
            CopilotSkill.visibility == Copilotskillvisibility.ORG,
            CopilotSkill.userId == uuid.UUID(ctx.user.id),
        )
    else:
        qspec = CopilotSkill.visibility == Copilotskillvisibility.ORG
    rows = (
        db.execute(
            select(CopilotSkill)
            .where(
                CopilotSkill.organizationId == org.id,
                qspec,
            )
            .order_by(CopilotSkill.updatedAt.desc())
            .limit(12)
        )
        .scalars()
        .all()
    )
    rt = (resourceType or "").strip()
    for s in rows:
        types = list(s.applicableResourceTypes or [])
        if types and rt and rt not in types:
            continue
        chips.append(
            {
                "id": f"skill:{s.id}",
                "label": s.title,
                "prompt": s.body,
                "kind": "skill",
                "skillId": str(s.id),
            }
        )
    # Optional: reorder with LLM (metadata only)
    if eff.get("enabled") and eff.get("baseUrl") and eff.get("apiKey") and len(chips) > 2:
        labels = ", ".join(c.get("label", "") for c in chips[:8])
        ranked = run_suggestion_titles(
            str(eff["baseUrl"]),
            str(eff["apiKey"]),
            str(eff.get("defaultModel") or "gpt-4.1-mini"),
            labels,
        )
        if ranked:
            # Best-effort: if model returned label-like order, we keep original order (skip fragile parse)
            pass
    return {"suggestions": chips[:12]}


# --- Skills ---


def _serialize_skill(s: CopilotSkill) -> dict[str, Any]:
    return {
        "id": str(s.id),
        "title": s.title,
        "description": s.description,
        "body": s.body,
        "visibility": s.visibility.value,
        "applicableResourceTypes": list(s.applicableResourceTypes or []),
        "userId": str(s.userId),
        "createdAt": s.createdAt.isoformat() if s.createdAt else None,
        "updatedAt": s.updatedAt.isoformat() if s.updatedAt else None,
    }


@router.get("/copilot/skills")
def list_skills(
    db: Session = Depends(get_db),
    auth: AuthContext | None = Depends(get_auth),
) -> dict[str, Any]:
    ctx = require_auth_ctx(auth)
    if not ctx.user:
        return {"items": []}
    uid = uuid.UUID(ctx.user.id)
    rows = (
        db.execute(
            select(CopilotSkill)
            .where(
                CopilotSkill.organizationId == ctx.organization.id,
                or_(
                    CopilotSkill.userId == uid,
                    CopilotSkill.visibility == Copilotskillvisibility.ORG,
                ),
            )
            .order_by(CopilotSkill.title.asc())
        )
        .scalars()
        .all()
    )
    return {"items": [_serialize_skill(s) for s in rows]}


@router.post("/copilot/skills")
def create_skill(
    body: Annotated[dict[str, Any], Body(...)],
    db: Session = Depends(get_db),
    auth: AuthContext | None = Depends(get_auth),
) -> dict[str, Any]:
    ctx = require_auth_ctx(auth)
    if not ctx.user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Skills require an interactive user session")
    title = str(body.get("title", "")).strip()
    sbody = str(body.get("body", "")).strip()
    if not title or not sbody:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="title and body required")
    vis_s = str(body.get("visibility", "PRIVATE")).upper()
    vis = (
        Copilotskillvisibility.ORG
        if vis_s == "ORG"
        else Copilotskillvisibility.PRIVATE
    )
    arts = body.get("applicableResourceTypes")
    if not isinstance(arts, list):
        arts = []
    s = CopilotSkill(
        id=uuid.uuid4(),
        organizationId=ctx.organization.id,
        userId=uuid.UUID(ctx.user.id),
        title=title,
        description=str(body.get("description", "") or "") or None,
        body=sbody,
        visibility=vis,
        applicableResourceTypes=[str(x) for x in arts if str(x).strip()][:20],
    )
    now = utc_now().replace(tzinfo=None)
    s.createdAt = now
    s.updatedAt = now
    db.add(s)
    record_audit(
        db,
        organization_id=ctx.organization.id,
        actor=auth_actor_from_context(ctx),
        action="CREATE",
        resource_type="CopilotSkill",
        resource_id=str(s.id),
        after={"title": s.title, "visibility": s.visibility.value},
    )
    db.commit()
    db.refresh(s)
    return _serialize_skill(s)


@router.patch("/copilot/skills/{skill_id}")
def patch_skill(
    skill_id: uuid.UUID,
    body: Annotated[dict[str, Any], Body(...)],
    db: Session = Depends(get_db),
    auth: AuthContext | None = Depends(get_auth),
) -> dict[str, Any]:
    ctx = require_auth_ctx(auth)
    if not ctx.user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Interactive user required")
    s = db.get(CopilotSkill, skill_id)
    if s is None or s.organizationId != ctx.organization.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
    uid = uuid.UUID(ctx.user.id)
    is_admin = ctx.role == Apitokenrole.ADMIN
    if s.userId != uid and not (is_admin and s.visibility == Copilotskillvisibility.ORG):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to edit this skill")

    if "title" in body and body["title"] is not None:
        t = str(body["title"]).strip()
        if t:
            s.title = t
    if "body" in body and body["body"] is not None and str(body["body"]).strip():
        s.body = str(body["body"]).strip()
    if "description" in body:
        s.description = str(body["description"] or "") or None
    if "visibility" in body and str(body.get("visibility", "")).upper() in ("ORG", "PRIVATE") and s.userId == uid:
        s.visibility = (
            Copilotskillvisibility.ORG if str(body["visibility"]).upper() == "ORG" else Copilotskillvisibility.PRIVATE
        )
    if "applicableResourceTypes" in body and isinstance(body["applicableResourceTypes"], list):
        s.applicableResourceTypes = [str(x) for x in body["applicableResourceTypes"] if str(x).strip()][:20]
    s.updatedAt = utc_now().replace(tzinfo=None)
    record_audit(
        db,
        organization_id=ctx.organization.id,
        actor=auth_actor_from_context(ctx),
        action="UPDATE",
        resource_type="CopilotSkill",
        resource_id=str(s.id),
        after={"title": s.title, "keysTouched": list(body.keys())},
    )
    db.commit()
    db.refresh(s)
    return _serialize_skill(s)


@router.delete("/copilot/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_skill(
    skill_id: uuid.UUID,
    db: Session = Depends(get_db),
    auth: AuthContext | None = Depends(get_auth),
) -> None:
    ctx = require_auth_ctx(auth)
    if not ctx.user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Interactive user required")
    s = db.get(CopilotSkill, skill_id)
    if s is None or s.organizationId != ctx.organization.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
    uid = uuid.UUID(ctx.user.id)
    is_admin = ctx.role == Apitokenrole.ADMIN
    if s.userId != uid and not (is_admin and s.visibility == Copilotskillvisibility.ORG):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to delete this skill")
    record_audit(
        db,
        organization_id=ctx.organization.id,
        actor=auth_actor_from_context(ctx),
        action="DELETE",
        resource_type="CopilotSkill",
        resource_id=str(s.id),
        after={"title": s.title},
    )
    db.delete(s)
    db.commit()
