"""Pasted-ticket / incident text: extract hostnames, IPs, search inventory (read-only)."""

from __future__ import annotations

import re
import uuid
from collections.abc import Iterator
from typing import Any

from sqlalchemy.orm import Session

from nims.services.global_search import global_search_items

_IPV4 = re.compile(
    r"(?<![0-9.])\b(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.("
    r"25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.("
    r"25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\b(?!\.[0-9])"
)
# Hostname-like: label.label.tld
_FQDN = re.compile(
    r"\b(?:[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?\.)+(?:[A-Za-z]{2,63}|[A-Za-z][A-Za-z-]*[A-Za-z])\b"
)


def _iter_terms(text: str) -> Iterator[str]:
    t = (text or "").strip()
    if not t or len(t) > 200_000:
        return
    seen: set[str] = set()
    for m in _IPV4.finditer(t):
        s = m.group(0)
        if s and s not in seen:
            seen.add(s)
            yield s
    for m in _FQDN.finditer(t):
        s = m.group(0).rstrip(".,;:")
        if len(s) < 4 or len(s) > 200:
            continue
        if s not in seen:
            seen.add(s)
            yield s


def build_triage_hits(
    db: Session,
    organization_id: uuid.UUID,
    pasted: str,
    per_term_limit: int = 5,
    max_terms: int = 12,
) -> dict[str, Any]:
    terms = list(_iter_terms(pasted))[: max(0, int(max_terms))]
    hits: list[dict[str, Any]] = []
    used_q: set[str] = set()
    for q in terms:
        q2 = str(q)[:200]
        if not q2 or q2 in used_q:
            continue
        used_q.add(q2)
        items = global_search_items(db, organization_id, q2, min(25, max(1, per_term_limit)))
        if items:
            hits.append(
                {
                    "query": q2,
                    "itemCount": len(items),
                    "items": items[:per_term_limit],
                }
            )
    return {
        "extractedTerms": terms,
        "searchBatches": hits,
        "readOnly": True,
    }
