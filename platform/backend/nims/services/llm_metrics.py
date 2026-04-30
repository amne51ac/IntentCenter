"""In-process LLM / copilot usage counters (admin metrics)."""

from __future__ import annotations

import threading
import time
from typing import Any

_lock = threading.Lock()
_stats: dict[str, Any] = {
    "copilotChatRequests": 0,
    "copilotStreamSessions": 0,
    "copilotToolCalls": 0,
    "importMappingRequests": 0,
    "ticketTriageRequests": 0,
    "internalLlmCompletions": 0,
    "llmErrors": 0,
    "serverEpochSec": 0,
}


def bump(name: str, n: int = 1) -> None:
    with _lock:
        if name not in _stats:
            _stats[name] = 0
        _stats[name] = int(_stats[name]) + n
        _stats["serverEpochSec"] = int(time.time())


def snapshot() -> dict[str, Any]:
    with _lock:
        out: dict[str, Any] = dict(_stats)
        out["serverEpochSec"] = int(time.time())
        return out


def error_bump() -> None:
    bump("llmErrors", 1)
