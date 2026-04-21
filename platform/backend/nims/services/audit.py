import uuid
from typing import Any

from sqlalchemy.orm import Session

from nims.json_util import to_input_json
from nims.models_generated import AuditEvent


def record_audit(
    db: Session,
    *,
    organization_id: uuid.UUID,
    actor: str,
    action: str,
    resource_type: str,
    resource_id: str,
    correlation_id: str | None = None,
    before: Any = None,
    after: Any = None,
) -> None:
    row = AuditEvent(
        id=uuid.uuid4(),
        organizationId=organization_id,
        actor=actor,
        action=action,
        resourceType=resource_type,
        resourceId=resource_id,
        correlationId=correlation_id,
        before=to_input_json(before) if before is not None else None,
        after=to_input_json(after) if after is not None else None,
    )
    db.add(row)
