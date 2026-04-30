"""OpenAI-compatible /v1/chat/completions with a tool-calling loop."""

from __future__ import annotations

import json
import logging
import os
from collections.abc import Iterator
from typing import Any

import httpx
from sqlalchemy.orm import Session

from nims.auth_context import AuthContext
from nims.services.copilot_tools import OPENAI_TOOL_DEFINITIONS, execute_copilot_tool
from nims.services.llm_metrics import error_bump
from nims.services.llm_url import (
    chat_completions_url,
    is_azure_openai_host,
    llm_request_headers,
    use_model_in_request_body,
)

log = logging.getLogger(__name__)

def _rounds() -> int:
    try:
        n = int(os.environ.get("COPILOT_MAX_TOOL_ROUNDS", "12").strip() or "12")
    except (TypeError, ValueError):
        return 12
    return max(1, min(n, 64))


def _build_copilot_system_text(page_context: dict[str, Any] | None) -> str:
    from nims.services.copilot_tools import build_context_block as _ctx

    return (
        "You are the Intent Center AI assistant for DCIM and network inventory. Use tools to obtain facts; do not "
        "invent counts, UUIDs, or object details.\n"
        "- **Tool rounds & multi-step reasoning:** You may use **several** tools in a row (multiple API rounds). For "
        "non-trivial questions, **plan**: (1) decide what sub-questions you need, (2) call the smallest read tools "
        "in sequence (e.g. `inventory_stats` → `catalog_breakdown` → `get_resource_view` for a few ids from `search`), "
        "(3) **merge** tool outputs in your final answer. Prefer completing the data-gathering pass before replying. "
        "If a single aggregate is not enough, chain tools rather than inventing numbers.\n"
        "- **Counts and 'how many' questions:** use the `inventory_stats` tool. It returns non-deleted object "
        "counts in the current organization. Pass `resource_type` (e.g. Device) to count one type, or omit it for all types.\n"
        "- **Finding objects by name, IP, CIDR, or identifier:** use `search` with a concrete `q` string. "
        "`search` matches text in display fields only; it is **not** a list of all devices and will often return no "
        "rows for generic words like 'device' if no object name contains that substring. For totals, use "
        "`inventory_stats`, not `search`.\n"
        "- **One object by type and id:** use `get_resource_view` or `get_resource_graph`.\n"
        "- **Full location tree / parent-child / map:** use `list_location_hierarchy` to get every location’s id, name, "
        "`parentId`, and any **latitude/longitude** in the data. Format an indented tree in Markdown, or a **map** "
        "(fenced `map` JSON with a markers array; center and zoom are optional because the app **auto-zooms to fit** "
        "all markers). If `locationsWithCoordinates` is 0, say coordinates are not set in the catalog rather than that "
        "the tool omits them.\n"
        "- **Grouped counts / charts (composable):** use **`catalog_breakdown`** with `query` set to one of the tool’s "
        "enum values, e.g. `Device/location`, `Device/device_type`, `Circuit/location` (distinct circuits per site with "
        "a termination; two-site circuits appear in both sites), `Circuit/provider`, `Circuit/status`, `Rack/location`. "
        "Use the returned `rows` for tables and `chart` blocks. **`device_count_breakdown`** is a legacy alias (same data "
        "via `group_by`). Do not say breakdown data is missing without calling `catalog_breakdown` first; if the `query` you "
        "need is not in the enum, say so and use other read tools, not guesswork.\n"
        "- **Proposed changes (read-only):** to describe planned writes for human review, use the `propose_change_preview` "
        "tool. It never mutates data; it returns a preview with current snapshots. Do not claim a change was applied.\n"
        "When you reference results, give object type, id, and a path like /o/Type/<uuid>. Be concise. English only. "
        "The only write proposal path is the preview tool; you cannot call mutating APIs.\n"
        "- **Formatting:** Reply in **Markdown** (headings, lists, tables, bold). For a **chart**, use a fenced block "
        "with language `chart` and a single JSON object. Schemas: (1) bar/line/area: v=1, kind, title, xKey, yKey, data. "
        "(2) pie: kind \"pie\", nameKey, valueKey, data. Only add charts for numbers you got from tools or the user, "
        "not made-up data. For a **change-plan card** the user can scan, you may use a fenced block with language "
        "`proposal` and JSON: {v:1, summary, changes: [{action, resource_type, resource_id?, rationale?}]}. "
        "For a small **geographic** map, use a fenced block with language `map` and a **single JSON object** "
        "(valid JSON: use `lng` or `longitude` for east/west, `lat` or `latitude` for north/south). "
        "Example: { \"title\": \"…\", \"markers\": [ { \"lat\": 0, \"lng\": 0, \"label\": \"…\" } ] }. "
        "Optional `center` and `zoom`. The UI auto-frames markers; only use coordinates from tools or the user.\n\n"
        f"{_ctx(page_context)}"
    )


def _init_copilot_messages(
    user_messages: list[dict[str, str]],
    page_context: dict[str, Any] | None,
) -> list[dict[str, Any]] | str:
    """
    Return messages array for the API, or a short string error/placeholder if the chat is empty.
    """
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": _build_copilot_system_text(page_context)},
    ]
    for m in user_messages[-20:]:
        r = m.get("role", "user")
        c = m.get("content", "")
        if r in ("user", "assistant") and isinstance(c, str):
            messages.append({"role": r, "content": c})
    if not any(m.get("role") == "user" for m in messages[1:]):
        return "Send a user message to continue."
    return messages


def _llm_config_error_text(base_url: str, status_code: int) -> str:
    if status_code == 404 and not is_azure_openai_host(base_url):
        extra = " Ensure the base URL includes the API version path, e.g. https://api.openai.com/v1."
    elif status_code == 404 and is_azure_openai_host(base_url):
        extra = (
            " For Azure, use the resource base URL (e.g. https://your-resource.openai.azure.com) "
            "and a default model that matches the deployment name."
        )
    else:
        extra = ""
    return f"LLM request failed ({status_code}). Check /platform/admin/llm configuration.{extra}"


def _def_line(line: str | bytes) -> str:
    if isinstance(line, bytes):
        return line.decode("utf-8", errors="replace")
    return line


def _string_from_message_content(c: Any) -> str:
    """OpenAI can return a string, or a list of content parts (e.g. Responses-style, multimodal)."""
    if c is None:
        return ""
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        out: list[str] = []
        for p in c:
            if isinstance(p, str):
                out.append(p)
            elif isinstance(p, dict):
                for key in ("text", "content", "value"):
                    v = p.get(key)
                    if isinstance(v, str) and v:
                        out.append(v)
        return "".join(out)
    if isinstance(c, dict) and isinstance(c.get("text"), str):
        return c["text"]
    return str(c)


def _delta_text_piece(d: dict[str, Any]) -> str:
    """Text from a streaming /chat/completions delta, including refusal and list-shaped content."""
    t = _string_from_message_content(d.get("content"))
    if t:
        return t
    for key in ("refusal", "reasoning", "reasoning_content", "thought"):
        v = d.get(key)
        if isinstance(v, str) and v.strip():
            return v
    im = d.get("message")
    if isinstance(im, dict):
        t2 = _string_from_message_content(im.get("content"))
        if t2:
            return t2
    return ""


def _assistant_message_text(msg: dict[str, Any]) -> str:
    """Usable text from a non-streaming choice ``message`` object."""
    t = _string_from_message_content(msg.get("content"))
    if t.strip():
        return t
    if isinstance(msg.get("refusal"), str) and msg["refusal"].strip():
        return str(msg["refusal"])
    return ""


def _openai_stream_chunk_to_text_and_tools(
    chunk: dict[str, Any],
) -> tuple[str, list[dict[str, Any]], str | None, str | None]:
    """
    From one streamed JSON object, return (text delta, tool_call deltas, finish_reason, top_level_error).
    """
    err_obj = chunk.get("error")
    if err_obj is not None:
        if isinstance(err_obj, dict):
            em = err_obj.get("message")
            return (
                "",
                [],
                None,
                str(em) if isinstance(em, str) else json.dumps(err_obj)[:500],
            )
        return ("", [], None, str(err_obj)[:500])
    choices = chunk.get("choices")
    if isinstance(choices, list) and len(choices) > 0 and isinstance(choices[0], dict):
        ch0: dict[str, Any] = choices[0]
    else:
        ch0 = {}
    fr = ch0.get("finish_reason")
    frs = str(fr) if fr is not None and fr else None
    d = ch0.get("delta") if isinstance(ch0.get("delta"), dict) else {}
    piece = _delta_text_piece(d) if d else ""
    tcs: list[dict[str, Any]] = []
    if d:
        for tcd in d.get("tool_calls") or []:
            if isinstance(tcd, dict):
                tcs.append(tcd)
    if not piece and not tcs and isinstance(ch0.get("message"), dict):
        m0 = ch0["message"]
        if isinstance(m0, dict):
            piece = _assistant_message_text(m0)
    if not piece and isinstance(ch0.get("text"), str):
        piece = ch0["text"]
    return piece, tcs, frs, None


def _sse_data_payload(s: str) -> str | None:
    """
    If ``s`` is an SSE ``data:`` line, return the payload; otherwise None.
    Tolerate ``data:`` with or without a space.
    """
    line = s.strip()
    if line.startswith("data: "):
        return line[6:].strip()
    if line.startswith("data:"):
        return line[5:].lstrip()
    return None


def _line_to_stream_payload(s: str) -> str | None:
    """``data: …`` SSE line, or a raw JSON line (NDJSON) from some gateways."""
    pl = _sse_data_payload(s)
    if pl is not None:
        return pl
    t = s.strip()
    if t.startswith("{") or t.startswith("["):
        return t
    return None


def _merge_stream_tool_block(blocks: dict[int, dict[str, Any]], dtc: dict[str, Any]) -> None:
    """Accumulate a streaming tool_call delta (OpenAI chat.completions)."""
    idx = int(dtc.get("index", 0) or 0)
    b = blocks.setdefault(
        idx,
        {
            "id": None,
            "type": "function",
            "function": {"name": "", "arguments": ""},
        },
    )
    if dtc.get("id"):
        b["id"] = dtc["id"]
    if dtc.get("type"):
        b["type"] = dtc["type"]
    fn = dtc.get("function")
    if not isinstance(fn, dict):
        return
    n = fn.get("name")
    if isinstance(n, str) and n:
        b["function"]["name"] = (b["function"]["name"] or "") + n
    a = fn.get("arguments")
    if isinstance(a, str) and a:
        b["function"]["arguments"] = (b["function"]["arguments"] or "") + a


def _tool_blocks_to_openai_list(blocks: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for k in sorted(blocks.keys()):
        b = blocks[k]
        out.append(
            {
                "id": str(b.get("id") or f"call_{k}"),
                "type": str(b.get("type") or "function"),
                "function": {
                    "name": b["function"]["name"],
                    "arguments": b["function"]["arguments"] or "",
                },
            }
        )
    return out


def _append_assistant_and_tool_results(
    db: Session,
    ctx: AuthContext,
    messages: list[dict[str, Any]],
    msg: dict[str, Any],
) -> None:
    """Append the assistant `message` and each tool result (mutates `messages`)."""
    messages.append(msg)
    for tc in msg.get("tool_calls") or []:
        fn = tc.get("function") or {}
        name = str(fn.get("name", ""))
        raw = fn.get("arguments")
        if isinstance(raw, str):
            try:
                args = json.loads(raw) if raw.strip() else {}
            except json.JSONDecodeError:
                args = {}
        elif isinstance(raw, dict):
            args = raw
        else:
            args = {}
        out = execute_copilot_tool(db, ctx, name, args)
        messages.append(
            {
                "role": "tool",
                "tool_call_id": str(tc.get("id") or "call"),
                "content": out,
            }
        )


def _recover_nonempty_assistant_reply(
    client: httpx.Client,
    base_url: str,
    api_key: str,
    model: str,
    messages: list[dict[str, Any]],
) -> str | None:
    """
    Text-only follow-up (no tools) if the main completion returned empty text — reduces 'No content from model'
    on some providers for very short or ambiguous user turns.
    """
    nudge: list[dict[str, Any]] = list(messages)
    nudge.append(
        {
            "role": "user",
            "content": (
                "Your previous reply was empty, which is not allowed. Respond with 1–3 short sentences in English. "
                "If the user is testing the chat, greet them and offer to help with inventory, DCIM, or search."
            ),
        }
    )
    body: dict[str, Any] = {
        "messages": nudge,
        "max_tokens": 400,
        "temperature": 0.45,
    }
    if use_model_in_request_body(base_url):
        body["model"] = model
    url = chat_completions_url(base_url, deployment=model)
    if not url:
        return None
    r = client.post(
        url,
        headers=llm_request_headers(base_url, api_key),
        json=body,
    )
    if r.status_code >= 400:
        return None
    raw_msg = (r.json().get("choices") or [{}])[0].get("message") or {}
    t = _assistant_message_text(raw_msg) if isinstance(raw_msg, dict) else ""
    s = (t or "").strip()
    return s or None


def _one_completion_non_streaming(
    client: httpx.Client,
    base_url: str,
    api_key: str,
    model: str,
    messages: list[dict[str, Any]],
) -> dict[str, Any] | str:
    body: dict[str, Any] = {
        "messages": messages,
        "tools": OPENAI_TOOL_DEFINITIONS,
        "tool_choice": "auto",
    }
    if use_model_in_request_body(base_url):
        body["model"] = model
    url = chat_completions_url(base_url, deployment=model)
    if not url:
        return (
            "LLM is misconfigured: for Azure OpenAI, set a default model / deployment name "
            "(e.g. your deployment in Azure) and a base URL like https://<resource>.openai.azure.com"
        )
    r = client.post(
        url,
        headers=llm_request_headers(base_url, api_key),
        json=body,
    )
    if r.status_code >= 400:
        log.warning("llm error %s: %s", r.status_code, r.text[:500])
        error_bump()
        return _llm_config_error_text(base_url, r.status_code)
    return r.json()


def _fake_deltas_for_text(text: str, step: int = 48) -> Iterator[dict[str, Any]]:
    t = str(text)
    for i in range(0, len(t), max(1, step)):
        yield {"type": "delta", "text": t[i : i + step]}


def iter_copilot_chat_sse(
    db: Session,
    ctx: AuthContext,
    base_url: str,
    api_key: str,
    model: str,
    user_messages: list[dict[str, str]],
    page_context: dict[str, Any] | None,
) -> Iterator[dict[str, Any]]:
    """
    Yields event dicts: ``delta`` (text chunks), ``status`` (e.g. tool use), ``error``,
    and final ``done`` (ok or after error). SSE wrapper adds framing.
    """
    init = _init_copilot_messages(user_messages, page_context)
    if isinstance(init, str):
        # User-side validation (e.g. empty turn); not counted as an LLM failure.
        yield {"type": "error", "message": init}
        yield {"type": "done"}
        return
    messages = list(init)
    with httpx.Client(timeout=httpx.Timeout(120.0, connect=20.0)) as client:
        for _ in range(_rounds()):
            sbody: dict[str, Any] = {
                "messages": messages,
                "tools": OPENAI_TOOL_DEFINITIONS,
                "tool_choice": "auto",
                "stream": True,
            }
            if use_model_in_request_body(base_url):
                sbody["model"] = model
            url = chat_completions_url(base_url, deployment=model)
            if not url:
                error_bump()
                msg = (
                    "LLM is misconfigured: for Azure OpenAI, set a default model / deployment name "
                    "(e.g. your deployment in Azure) and a base URL like https://<resource>.openai.azure.com"
                )
                yield {"type": "error", "message": msg}
                yield {"type": "done"}
                return
            content_parts: list[str] = []
            tool_blocks: dict[int, dict[str, Any]] = {}
            finish_reason: str | None = None
            fallback_json: dict[str, Any] | None = None
            try:
                with client.stream(
                    "POST",
                    url,
                    headers=llm_request_headers(base_url, api_key),
                    json=sbody,
                ) as r:
                    if r.status_code >= 400:
                        (r.read() or b"").decode("utf-8", errors="replace")[:500]
                        log.warning("llm stream HTTP %s; trying non-streaming for this round", r.status_code)
                        ns = _one_completion_non_streaming(client, base_url, api_key, model, messages)
                        if isinstance(ns, str):
                            error_bump()
                            yield {"type": "error", "message": ns}
                            yield {"type": "done"}
                            return
                        fallback_json = ns
                    elif r.status_code < 400:
                        for line in r.iter_lines():
                            s = _def_line(line) if line else ""
                            s = s.lstrip("\ufeff").strip()
                            if s == "[DONE]":
                                break
                            data = _line_to_stream_payload(s)
                            if data is None or not data:
                                continue
                            if data == "[DONE]":
                                break
                            try:
                                chunk: dict[str, Any] = json.loads(data)
                            except json.JSONDecodeError:
                                continue
                            piece, tcd_list, fr_stream, stream_err = _openai_stream_chunk_to_text_and_tools(chunk)
                            if stream_err:
                                error_bump()
                                yield {"type": "error", "message": stream_err}
                                yield {"type": "done"}
                                return
                            if fr_stream is not None and fr_stream:
                                finish_reason = fr_stream
                            if piece:
                                content_parts.append(piece)
                                yield {"type": "delta", "text": piece}
                            for tcd in tcd_list:
                                _merge_stream_tool_block(tool_blocks, tcd)
            except httpx.ReadError as e:
                log.warning("llm stream read: %s", e)
                error_bump()
                yield {"type": "error", "message": f"LLM stream interrupted: {e!s}."}
                yield {"type": "done"}
                return
            if fallback_json is not None:
                choice = (fallback_json.get("choices") or [{}])[0]
                msg = choice.get("message") or {}
                tcs = msg.get("tool_calls")
                if tcs:
                    yield {"type": "status", "text": "Using inventory tools…"}
                    _append_assistant_and_tool_results(db, ctx, messages, msg)
                    continue
                final = _assistant_message_text(msg)
                for ev in _fake_deltas_for_text(final, 64):
                    yield ev
                if not final.strip():
                    recovered2 = _recover_nonempty_assistant_reply(client, base_url, api_key, model, messages)
                    if recovered2:
                        for ev in _fake_deltas_for_text(recovered2, 64):
                            yield ev
                    else:
                        error_bump()
                        yield {"type": "error", "message": "No content from model."}
                yield {"type": "done"}
                return
            text_joined = "".join(content_parts)
            has_tools = bool(tool_blocks) and any(
                (tool_blocks.get(i) or {}).get("function", {}).get("name", "").strip() for i in tool_blocks
            )
            fr2 = (finish_reason or "stop").lower()
            # If the stream had no decodable text (or proxy stripped chunks), get one non-streaming completion.
            if not (text_joined or "").strip() and fr2 != "tool_calls" and not has_tools:
                ns_rec = _one_completion_non_streaming(client, base_url, api_key, model, messages)
                if isinstance(ns_rec, str):
                    error_bump()
                    yield {"type": "error", "message": ns_rec}
                    yield {"type": "done"}
                    return
                rmsg = (ns_rec.get("choices") or [{}])[0].get("message") or {}
                tcs2 = rmsg.get("tool_calls")
                if tcs2:
                    yield {"type": "status", "text": "Using inventory tools…"}
                    _append_assistant_and_tool_results(db, ctx, messages, rmsg)
                    continue
                recovered = _assistant_message_text(rmsg).strip()
                if recovered:
                    for ev in _fake_deltas_for_text(recovered, 64):
                        yield ev
                else:
                    recovered2 = _recover_nonempty_assistant_reply(client, base_url, api_key, model, messages)
                    if recovered2:
                        for ev in _fake_deltas_for_text(recovered2, 64):
                            yield ev
                    else:
                        error_bump()
                        yield {"type": "error", "message": "No content from model."}
                yield {"type": "done"}
                return
            if fr2 == "tool_calls" or has_tools:
                tcl = _tool_blocks_to_openai_list(tool_blocks)
                a_msg: dict[str, Any] = {
                    "role": "assistant",
                    "content": text_joined or None,
                    "tool_calls": tcl,
                }
                if a_msg.get("content") is None:
                    a_msg.pop("content", None)
                yield {"type": "status", "text": "Using inventory tools…"}
                _append_assistant_and_tool_results(db, ctx, messages, a_msg)
                continue
            if not (text_joined or "").strip():
                recovered2 = _recover_nonempty_assistant_reply(client, base_url, api_key, model, messages)
                if recovered2:
                    for ev in _fake_deltas_for_text(recovered2, 64):
                        yield ev
                else:
                    error_bump()
                    yield {"type": "error", "message": "No content from model."}
            yield {"type": "done"}
            return
        error_bump()
        yield {"type": "error", "message": "Tool round limit reached. Try a narrower question."}
        yield {"type": "done"}


def run_copilot_chat(
    db: Session,
    ctx: AuthContext,
    base_url: str,
    api_key: str,
    model: str,
    user_messages: list[dict[str, str]],
    page_context: dict[str, Any] | None,
) -> str:
    """
    user_messages: list of {role: user|assistant, content: str} from the client (last turns).
    """
    init = _init_copilot_messages(user_messages, page_context)
    if isinstance(init, str):
        return init
    messages = init

    with httpx.Client(timeout=httpx.Timeout(120.0, connect=20.0)) as client:
        for _round_n in range(_rounds()):
            data = _one_completion_non_streaming(client, base_url, api_key, model, messages)
            if isinstance(data, str):
                return data
            choice = (data.get("choices") or [{}])[0]
            msg = choice.get("message") or {}
            tcs = msg.get("tool_calls")
            if tcs:
                _append_assistant_and_tool_results(db, ctx, messages, msg)
                continue
            final = _assistant_message_text(msg).strip()
            if not final:
                r2 = _recover_nonempty_assistant_reply(client, base_url, api_key, model, messages)
                final = (r2 or "").strip() or "No content from model."
            if final == "No content from model.":
                error_bump()
            return final
        error_bump()
        return "Tool round limit reached. Try a narrower question."


def run_suggestion_titles(
    base_url: str,
    api_key: str,
    model: str,
    chip_labels: str,
) -> str | None:
    """Optionally re-rank a tiny metadata-only prompt. Returns None on failure (caller uses defaults)."""
    url = chat_completions_url(base_url, deployment=model)
    if not url:
        return None
    jbody: dict[str, Any] = {
        "messages": [
            {
                "role": "user",
                "content": f"Output only a comma-separated list, no other text, ordering these from most to least useful on this page: {chip_labels}",  # noqa: E501
            }
        ],
    }
    if use_model_in_request_body(base_url):
        jbody["model"] = model
    with httpx.Client(timeout=httpx.Timeout(20.0, connect=5.0)) as client:
        r = client.post(
            url,
            headers=llm_request_headers(base_url, api_key),
            json=jbody,
        )
        if r.status_code >= 400:
            return None
        c = (r.json().get("choices") or [{}])[0].get("message", {}).get("content")
        return str(c).strip() if c else None


def run_suggest_thread_title(
    base_url: str,
    api_key: str,
    model: str,
    user_message: str,
    assistant_message: str,
) -> str | None:
    """One completion: a short list title for the first user/assistant turn. Returns None on failure."""
    u = (user_message or "").strip()[:4000]
    a = (assistant_message or "").strip()[:12_000]
    if not u:
        return None
    system = (
        "You name chat threads for a DCIM and network inventory assistant. "
        "Output exactly one line: a short title (3 to 8 words). No quotes, no trailing period, English only. "
        "Focus on the user's request or the topic, not the words 'chat' or 'thread'."
    )
    user_content = f"User message:\n{u}\n\nAssistant reply (may be long; title from the main topic):\n{a[:3000]}"
    url = chat_completions_url(base_url, deployment=model)
    if not url:
        return None
    jbody: dict[str, Any] = {
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
        "max_tokens": 48,
        "temperature": 0.2,
    }
    if use_model_in_request_body(base_url):
        jbody["model"] = model
    with httpx.Client(timeout=httpx.Timeout(30.0, connect=8.0)) as client:
        r = client.post(
            url,
            headers=llm_request_headers(base_url, api_key),
            json=jbody,
        )
        if r.status_code >= 400:
            return None
        raw = (r.json().get("choices") or [{}])[0].get("message", {}).get("content")
        if not raw:
            return None
        line = str(raw).strip().split("\n", 1)[0].strip()
        line = line.strip('"').strip("'").rstrip("….").strip()
        if not line:
            return None
        if len(line) > 80:
            line = line[:77] + "…"
        return line


def _parse_next_steps_json(text: str) -> list[dict[str, Any]]:
    """Parse model output into 3 {id, label, prompt} items, or []."""
    t = (text or "").strip()
    if t.startswith("```"):
        parts = t.split("```", 2)
        if len(parts) >= 2:
            t = parts[1]
            if t.lower().startswith("json"):
                t = t[4:].lstrip()
    t = t.strip()
    start = t.find("{")
    if start < 0:
        return []
    for attempt in (t[start:], t):
        try:
            data = json.loads(attempt)
        except json.JSONDecodeError:
            continue
        s = data.get("suggestions")
        if not isinstance(s, list):
            continue
        out: list[dict[str, Any]] = []
        for i, o in enumerate(s):
            if not isinstance(o, dict):
                continue
            label = str(o.get("label", "")).strip()
            pr = str(o.get("prompt", label)).strip()
            if not pr:
                continue
            out.append(
                {
                    "id": str(o.get("id", f"next_{i + 1}"))[:64],
                    "label": (label or pr)[:100],
                    "prompt": pr[:2000],
                }
            )
            if len(out) == 3:
                return out
        if out:
            return out
    return []


def run_suggest_next_steps(
    base_url: str,
    api_key: str,
    model: str,
    page_situation: str,
    chat_transcript: str,
) -> list[dict[str, Any]]:
    """
    Propose exactly 3 follow-up user intents as JSON. Returns [] on failure.
    page_situation: route + server-enriched what the user is looking at.
    chat_transcript: last turns formatted as plain text, capped in size.
    """
    if not (page_situation or "").strip() and not (chat_transcript or "").strip():
        return []
    system = (
        "You are helping users navigate the IntentCenter DCIM/inventory web app. "
        "The in-app assistant can use tools: search, inventory_stats, get_resource_view, get_resource_graph, "
        "list_location_hierarchy, catalog_breakdown (composable counts by Entity/dimension), device_count_breakdown, "
        "propose_change_preview. "
        "Propose exactly 3 different, concrete next questions or actions the user could take, "
        "informed by the app page/screen and the recent chat. "
        "Vary the intent (e.g. counts vs search vs relationships vs next object). "
        "Each option must be useful if pasted as a user message to the assistant. "
        "Output a **single JSON object** only, no markdown fences, in this form:\n"
        '{"suggestions":[{"id":"1","label":"4-8 word chip text","prompt":"Full user message to send to the assistant."},...]}'  # noqa: E501
        "\nExactly 3 objects in the suggestions array. English. Short labels; prompts may be 1-3 sentences."
    )
    user_c = f"## Page and screen\n{page_situation[:6000]}\n\n## Recent chat\n{chat_transcript[:8000] or '(no messages yet)'}\n"
    url = chat_completions_url(base_url, deployment=model)
    if not url:
        return []
    jbody: dict[str, Any] = {
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_c},
        ],
        "max_tokens": 450,
        "temperature": 0.5,
    }
    if use_model_in_request_body(base_url):
        jbody["model"] = model
    jbody_json: dict[str, Any] = {**jbody, "response_format": {"type": "json_object"}}
    with httpx.Client(timeout=httpx.Timeout(45.0, connect=10.0)) as client:
        r = client.post(
            url,
            headers=llm_request_headers(base_url, api_key),
            json=jbody_json,
        )
        if r.status_code >= 400:
            r = client.post(
                url,
                headers=llm_request_headers(base_url, api_key),
                json=jbody,
            )
        if r.status_code >= 400:
            return []
        raw = (r.json().get("choices") or [{}])[0].get("message", {}).get("content")
        if not raw:
            return []
        return _parse_next_steps_json(str(raw))


def run_text_completion(
    base_url: str,
    api_key: str,
    model: str,
    messages: list[dict[str, str]],
    max_tokens: int = 4096,
    temperature: float = 0.2,
) -> str | None:
    """
    No tools. For internal/extension callers. Returns None on transport or HTTP error;
    the caller can record `error_bump()` if they treat that as a failure.
    """
    clean: list[dict[str, str]] = []
    for m in messages[-40:]:
        if not isinstance(m, dict):
            continue
        r = m.get("role", "")
        c = m.get("content", "")
        if r not in ("system", "user", "assistant") or not isinstance(c, str):
            continue
        clean.append({"role": r, "content": c})
    if not any(m.get("role") == "user" for m in clean):
        return None
    url = chat_completions_url(base_url, deployment=model)
    if not url:
        return None
    jbody: dict[str, Any] = {
        "messages": clean,
        "max_tokens": max(64, min(max_tokens, 64_000)),
        "temperature": min(2.0, max(0.0, float(temperature))),
    }
    if use_model_in_request_body(base_url):
        jbody["model"] = model
    with httpx.Client(timeout=httpx.Timeout(120.0, connect=20.0)) as client:
        r = client.post(
            url,
            headers=llm_request_headers(base_url, api_key),
            json=jbody,
        )
        if r.status_code >= 400:
            return None
        out = (r.json().get("choices") or [{}])[0].get("message", {}).get("content")
        return str(out).strip() if out else None


def _parse_column_mapping_result(text: str) -> dict[str, Any] | None:
    t = (text or "").strip()
    if t.startswith("```"):
        parts = t.split("```", 2)
        if len(parts) >= 2:
            t = parts[1]
            if t.lower().startswith("json"):
                t = t[4:].lstrip()
    t = t.strip()
    start = t.find("{")
    if start < 0:
        return None
    for cut in (t[start:], t):
        try:
            o = json.loads(cut)
        except json.JSONDecodeError:
            continue
        if isinstance(o, dict) and "columnMapping" in o and isinstance(o.get("columnMapping"), dict):
            return o
        if isinstance(o, dict) and "mappings" in o and isinstance(o.get("mappings"), dict):
            return {"columnMapping": o["mappings"], "notes": o.get("notes")}
    return None


def run_import_column_mapping(
    base_url: str,
    api_key: str,
    model: str,
    target_resource_type: str,
    columns: list[str],
    sample_rows: list[dict[str, str]],
) -> dict[str, Any] | None:
    t_rt = (target_resource_type or "").strip()[:120]
    cols = [str(c)[:200] for c in columns if str(c).strip()][:80]
    rows = sample_rows[:20]
    system = (
        "You map incoming spreadsheet/CSV column headers to a target resource type. "
        "Output valid JSON only, no markdown, with this form:\n"
        '{"columnMapping": {"<column header>": "<logical field or attribute name>"}, '
        '"unmapped": ["<column>"], "notes": "<short confidence notes>"}.\n'
        "Map only columns you can reason about; list uncertain columns in unmapped."
    )
    user_c = f"Target resource type: {t_rt}\n\n## Columns\n{json.dumps(cols)[:12_000]}\n\n## Sample rows (objects)\n{json.dumps(rows, default=str)[:20_000]}\n"  # noqa: E501
    url = chat_completions_url(base_url, deployment=model)
    if not url:
        return None
    jbody: dict[str, Any] = {
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_c},
        ],
        "max_tokens": 1800,
        "temperature": 0.1,
    }
    if use_model_in_request_body(base_url):
        jbody["model"] = model
    with httpx.Client(timeout=httpx.Timeout(60.0, connect=10.0)) as client:
        r = client.post(
            url,
            headers=llm_request_headers(base_url, api_key),
            json=jbody,
        )
        if r.status_code >= 400:
            return None
        raw = (r.json().get("choices") or [{}])[0].get("message", {}).get("content")
        if not raw:
            return None
        return _parse_column_mapping_result(str(raw))


def run_ticket_triage_summary(
    base_url: str,
    api_key: str,
    model: str,
    pasted: str,
    triage_hits: dict[str, Any],
) -> str | None:
    p = (pasted or "").strip()[:24_000]
    hits = json.dumps(triage_hits, default=str)[:20_000]
    system = (
        "You summarize a pasted support ticket for a DCIM and network inventory operator. "
        "Be practical: what was extracted, which inventory search hits are relevant, what to check next. "
        "3–6 short bullet points, Markdown, English. Do not invent data not in the input."
    )
    user_c = f"## Pasted text\n{p}\n\n## Extracted / search (JSON)\n{hits}\n"
    url = chat_completions_url(base_url, deployment=model)
    if not url:
        return None
    jbody: dict[str, Any] = {
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_c},
        ],
        "max_tokens": 800,
        "temperature": 0.25,
    }
    if use_model_in_request_body(base_url):
        jbody["model"] = model
    with httpx.Client(timeout=httpx.Timeout(45.0, connect=10.0)) as client:
        r = client.post(
            url,
            headers=llm_request_headers(base_url, api_key),
            json=jbody,
        )
        if r.status_code >= 400:
            return None
        raw = (r.json().get("choices") or [{}])[0].get("message", {}).get("content")
        if not raw:
            return None
        return str(raw).strip() or None
