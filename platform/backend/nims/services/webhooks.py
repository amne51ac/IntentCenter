import hashlib
import hmac
import json
import logging
import threading
import uuid
from datetime import UTC, datetime
from typing import Any, Literal

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from nims.models_generated import Webhookevent, WebhookSubscription

logger = logging.getLogger(__name__)

EventKind = Literal["create", "update", "delete"]


def _sign_body(secret: str, body: str) -> str:
    return hmac.new(secret.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).hexdigest()


_event_map: dict[EventKind, Webhookevent] = {
    "create": Webhookevent.CREATE,
    "update": Webhookevent.UPDATE,
    "delete": Webhookevent.DELETE,
}


def dispatch_webhooks(
    db: Session,
    *,
    organization_id: uuid.UUID,
    resource_type: str,
    resource_id: str,
    event: EventKind,
    diff: dict[str, Any] | None = None,
) -> None:
    payload: dict[str, Any] = {
        "event": event,
        "resourceType": resource_type,
        "resourceId": resource_id,
        "organizationId": str(organization_id),
        "at": datetime.now(UTC).isoformat(),
    }
    if diff is not None:
        payload["diff"] = diff
    body = json.dumps(payload, separators=(",", ":"))

    subs = (
        db.execute(
            select(WebhookSubscription).where(
                WebhookSubscription.organizationId == organization_id,
                WebhookSubscription.enabled.is_(True),
            )
        )
        .scalars()
        .all()
    )

    want = _event_map[event]
    to_send: list[tuple[str, str, dict[str, str]]] = []
    for sub in subs:
        evs = sub.events or []
        if want not in evs:
            continue
        rts = sub.resourceTypes or []
        if rts and resource_type not in rts:
            continue
        headers = {
            "Content-Type": "application/json",
            "X-NIMS-Event": event,
            "X-NIMS-Resource": resource_type,
        }
        if sub.secret:
            headers["X-NIMS-Signature"] = f"sha256={_sign_body(sub.secret, body)}"
        to_send.append((str(sub.id), sub.url, headers))

    if not to_send:
        return

    def _sync_run() -> None:
        with httpx.Client(timeout=30.0) as client:
            for sub_id, url, headers in to_send:
                try:
                    res = client.post(url, headers=headers, content=body)
                    if res.status_code >= 400:
                        logger.warning("webhook %s failed %s", sub_id, res.status_code)
                except Exception as e:
                    logger.warning("webhook %s error %s", sub_id, e)

    threading.Thread(target=_sync_run, daemon=True).start()
