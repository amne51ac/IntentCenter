"""Internal LLM completion for extensions / workers (API key + organization scope)."""

from __future__ import annotations

import os
import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from nims.deps import get_db
from nims.models_generated import Organization
from nims.services.llm_config import get_effective_llm_for_runtime
from nims.services.llm_metrics import bump, error_bump
from nims.services.llm_openai import run_text_completion

router = APIRouter(tags=["internal"])


def _check_internal_key(x_nims_internal_key: str | None) -> None:
    expected = (os.environ.get("NIMS_INTERNAL_LLM_KEY") or "").strip()
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Internal LLM is not configured (set NIMS_INTERNAL_LLM_KEY in the server environment).",
        )
    if not x_nims_internal_key or x_nims_internal_key.strip() != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing X-Nims-Internal-Key.")


@router.post("/internal/llm/complete")
def post_internal_llm_complete(
    body: Annotated[dict[str, Any], Body(...)],
    db: Session = Depends(get_db),
    x_nims_internal_key: str | None = Header(None, alias="X-Nims-Internal-Key"),
    x_organization_id: str = Header(..., alias="X-Organization-Id"),
) -> dict[str, Any]:
    """
    Text-only completion using the target org's effective LLM (no tools). For workers and extension runtimes.
    Headers: ``X-Nims-Internal-Key``, ``X-Organization-Id`` (UUID).
    Body: ``{ "messages": [ { "role": "system"|"user"|"assistant", "content": "..." } ], "maxTokens"?: int, "temperature"?: float }``
    """
    _check_internal_key(x_nims_internal_key)
    try:
        oid = uuid.UUID(str(x_organization_id).strip())
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="X-Organization-Id must be a UUID") from e
    org = db.get(Organization, oid)
    if org is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    eff = get_effective_llm_for_runtime(org)
    if not eff.get("enabled"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM is not enabled for this organization.",
        )
    if not eff.get("baseUrl") or not eff.get("apiKey"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM is not fully configured (base URL and API key required).",
        )
    raw_m = body.get("messages")
    if not isinstance(raw_m, list) or not raw_m:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="messages array required")
    msgs: list[dict[str, str]] = []
    for m in raw_m[-40:]:
        if not isinstance(m, dict):
            continue
        role = m.get("role")
        content = m.get("content")
        if role in ("system", "user", "assistant") and isinstance(content, str):
            msgs.append({"role": str(role), "content": content})
    if not any(x.get("role") == "user" for x in msgs):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one user message is required")
    try:
        max_t = int(body.get("maxTokens") or body.get("max_tokens") or 4096)
    except (TypeError, ValueError):
        max_t = 4096
    try:
        temp = float(body.get("temperature", 0.2))
    except (TypeError, ValueError):
        temp = 0.2
    text = run_text_completion(
        str(eff["baseUrl"]),
        str(eff["apiKey"]),
        str(eff.get("defaultModel") or "gpt-4.1-mini"),
        msgs,
        max_tokens=max_t,
        temperature=temp,
    )
    if text is None:
        error_bump()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="LLM completion failed or returned no content.",
        )
    bump("internalLlmCompletions", 1)
    return {"message": {"role": "assistant", "content": text}}
