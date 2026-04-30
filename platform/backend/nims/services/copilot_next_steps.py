"""
Context extraction and heuristic "next step" suggestions for the copilot chips.

Keeps follow-ups **specific to the last chat turns and the object page** instead of
generic org-wide inventory when we can infer intent from keywords.
"""

from __future__ import annotations

import re
from typing import Any

_MAX_TURN = 1_200


def _transcript_segments(text: str) -> list[tuple[str, str]]:
    """(USER|ASSISTANT, body) in order, matching ``_format_messages_for_next_steps`` (``ROLE: body`` at line start)."""
    t = (text or "").strip()
    if not t:
        return []
    m = list(re.finditer(r"^(USER|ASSISTANT)\s*:\s*", t, re.MULTILINE | re.IGNORECASE))
    out: list[tuple[str, str]] = []
    for i, mm in enumerate(m):
        start = mm.end()
        end = m[i + 1].start() if i + 1 < len(m) else len(t)
        role = re.sub(r"\s+", "", mm.group(1)).upper()
        if role not in ("USER", "ASSISTANT"):
            continue
        out.append((role, t[start:end].strip()))
    if not m:
        p = t.split(":", 1)
        if len(p) == 2 and p[0].strip().upper() in ("USER", "ASSISTANT"):
            return [(p[0].strip().upper(), p[1].strip()[:_MAX_TURN])]
    return out


def extract_last_labeled_block(transcript: str, label: str) -> str:
    """`label` is ``USER`` or ``ASSISTANT`` as in the formatted chat transcript."""
    want = label.upper()
    for role, body in reversed(_transcript_segments(transcript or "")):
        if role == want:
            return body[:_MAX_TURN]
    return ""


def extract_last_user_text(transcript: str) -> str:
    return extract_last_labeled_block(transcript, "USER")


def extract_last_assistant_text(transcript: str) -> str:
    return extract_last_labeled_block(transcript, "ASSISTANT")


def _append_unique(
    out: list[dict[str, Any]], item: dict[str, Any], seen: set[str], at_most: int = 3
) -> None:
    if len(out) >= at_most:
        return
    key = item.get("id", "") + (item.get("label") or "")
    if key in seen:
        return
    seen.add(key)
    out.append(item)


def build_heuristic_suggestion_chips(
    page_s: str, chat_t: str
) -> list[dict[str, Any]] | None:
    """
    Return up to 3 *specific* chips from chat + page; None to fall back to the generic pool.
    Prefer to return a full 3; callers may still pad.
    """
    cl = (chat_t or "").lower()
    if len((chat_t or "").strip()) < 6 and "Object shown in the UI" not in (page_s or ""):
        return None
    has_obj = "Object shown in the UI" in (page_s or "")
    last_u = extract_last_user_text(chat_t or "")
    last_a = extract_last_assistant_text(chat_t or "")
    out: list[dict[str, Any]] = []
    seen: set[str] = set()

    if (
        re.search(r"interface|interfaces|nics?\b|network interface", cl)
        and re.search(
            r"without|missing|no interface|not have|don\x27t have|don t have|attach|"
            r"network interface|catalog_list|without_interface",
            cl,
        )
    ) or re.search(
        r"devices? that don\x27t have|devices? with no|no .{0,24}interface",
        cl,
    ):
        _append_unique(
            out,
            {
                "id": "h_no_if",
                "label": "Devices with no interface records",
                "prompt": (
                    "Use `catalog_list` with query `Device/without_interfaces` and `limit` 200. If truncated, report "
                    "`totalCount` and show a table from `rows` with name, status, and location. Do not use generic org "
                    "totals; stay on this list."
                ),
            },
            seen,
        )
    if re.search(r"catalog_list|Device/without", cl):
        _append_unique(
            out,
            {
                "id": "h_rerun_list",
                "label": "Rerun the same list with a higher cap",
                "prompt": (
                    "Call `catalog_list` again for `Device/without_interfaces` with a higher `limit` (up to 200) and say "
                    "if `totalCount` still exceeds what we can show in chat."
                ),
            },
            seen,
        )
    if re.search(r"provider|by provider|carrier", cl):
        _append_unique(
            out,
            {
                "id": "h_prov",
                "label": "Circuit counts by provider",
                "prompt": (
                    "Run `catalog_breakdown` with query `Circuit/provider` and summarize the top providers from tool "
                    "output only, with a small chart or table."
                ),
            },
            seen,
        )
    if re.search(r"per site|by site|per location|by location|each site", cl) and re.search(
        r"device|circuit|rack", cl
    ):
        _append_unique(
            out,
            {
                "id": "h_site",
                "label": "Match-up: devices vs circuits by site",
                "prompt": (
                    "Call `catalog_breakdown` for `Device/location` and `Circuit/location`, then compare the busiest sites "
                    "in a short table. Use only numbers from the tools."
                ),
            },
            seen,
        )
    if has_obj and len(out) < 3:
        rt_m = re.search(
            r"Object shown in the UI:\s*([A-Za-z0-9_]+)", page_s or ""
        ) or re.search(
            r"object page:\s*([A-Za-z0-9_]+)", (page_s or ""), re.I
        )
        rt = rt_m.group(1) if rt_m else "this object"
        _append_unique(
            out,
            {
                "id": "h_graph",
                "label": f"Links & dependencies for {rt}",
                "prompt": (
                    f"I am on an object page for type {rt} with the id in the app URL. Use `get_resource_graph` (and if "
                    f"needed `get_resource_view`) to list what this object connects to and what depends on it, with types "
                    f"and ids. Suggest a deeper follow-up (one hop) in natural language—do not start with a generic org "
                    f"inventory request."
                ),
            },
            seen,
        )
    if last_u and len(last_u) > 15 and len(out) < 3:
        preview = (last_u[:64] + "…") if len(last_u) > 64 else last_u
        _append_unique(
            out,
            {
                "id": "h_dig",
                "label": "Go deeper on my last question",
                "prompt": (
                    f"I asked: {last_u}\n"
                    f"Please take the *next* concrete step toward that goal using the smallest set of read tools. "
                    f"Quote tool results; avoid generic 'inventory snapshot' or org-wide tour unless I asked for counts."
                ),
            },
            seen,
        )
    if last_a and re.search(
        r"can\x27t|cannot|not available|don\x27t have|missing tool|no tool", (last_a or ""), re.I
    ) and len(out) < 3:
        _append_unique(
            out,
            {
                "id": "h_gap",
                "label": "What we can do instead (same topic)",
                "prompt": (
                    f"The last assistant reply was limited. Re-read it; then list the *closest* alternatives I can do now "
                    f"with the available read tools, staying on the same topic (no generic 'show me the whole org')."
                ),
            },
            seen,
        )
    if len(out) < 1:
        return None
    if len(out) < 3:
        _append_unique(
            out,
            {
                "id": "h_search",
                "label": "Narrow with search on this thread",
                "prompt": (
                    f"From my recent question: { (last_u[:200] if last_u else 'my topic above') }, "
                    f"propose one concrete `search` query string (a hostname fragment, IP, or object name) and run "
                    f"search, then show the top 5 hits with types and links."
                ),
            },
            seen,
        )
    if len(out) < 3 and has_obj:
        _append_unique(
            out,
            {
                "id": "h_viz",
                "label": "Attributes & related objects",
                "prompt": (
                    "Use `get_resource_view` for the object in the app URL, then one focused follow-up that uses fields "
                    "or relationships the user is likely to care about next. Stay specific; no org-wide report."
                ),
            },
            seen,
        )
    if len(out) < 1:
        return None
    return out[:3]


def pad_suggestions_to_three(front: list[dict[str, Any]], h: int, has_object: bool) -> list[dict[str, Any]]:
    """
    If ``front`` has 1–2 specific chips, append from a small *generic* pool to reach 3, avoiding duplicate ids/labels.
    """
    if len(front) >= 3:
        return front[:3]
    out = list(front)
    seen = {d.get("id", "") + str(d.get("label", "")) for d in out}
    pool: list[dict[str, Any]] = [
        {
            "id": f"gen_{h%9}",
            "label": "Search a hostname, IP, or CIDR in inventory",
            "prompt": "Pick a concrete `search` query (hostname fragment, IP, or prefix) for something I am tracking in DCIM, run search, and list the first few hits with types and ids so I can open one.",
        },
    ]
    if has_object:
        pool.append(
            {
                "id": f"gen_obj_{h%5}",
                "label": "Export-style summary of this object’s fields",
                "prompt": "With `get_resource_view` for the object in the app URL, summarize the most important fields in a compact bullet list, then one concrete follow-up the user is likely to want next.",
            }
        )
    pool.append(
        {
            "id": f"gen_site_{h%7}",
            "label": "Compare device density across top sites",
            "prompt": "Run `catalog_breakdown` for `Device/location` and briefly call out the top 5 sites by device count—only as context if my chat did not already cover sites.",
        }
    )
    for s in pool:
        if len(out) >= 3:
            break
        k = s.get("id", "") + str(s.get("label", ""))
        if k in seen:
            continue
        seen.add(k)
        out.append(s)
    if len(out) < 3:
        out.extend(
            [
                {
                    "id": "gen_fill1",
                    "label": "Inventory totals (only if relevant)",
                    "prompt": "Only if the chat was about *counts*: run `inventory_stats` and summarize. Otherwise prefer a narrower tool tied to my last question above.",
                }
            ]
        )
    return out[:3]


def build_next_steps_user_content(
    page_s: str, chat_t: str, last_user: str, last_asst: str, max_chat: int
) -> str:
    bu = f"\n## Last user turn (highest priority for your chip prompts)\n{last_user or '(not available)'}\n"
    ba = f"\n## Last assistant turn (suggest *follow-ups to this* — not a generic org tour)\n{last_asst or '(not available)'}\n"
    ct = (chat_t or "")[:max_chat] or "(no messages yet)"
    return f"## Page and screen\n{(page_s or '(none)')[:6000]}{bu}{ba}## Full chat transcript (most recent last)\n{ct}\n"
