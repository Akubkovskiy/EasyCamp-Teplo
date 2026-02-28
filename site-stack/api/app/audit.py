import json
from sqlalchemy.orm import Session
from .models import AdminAuditLog


def log_action(db: Session, entity: str, action: str, entity_id: int | None = None, payload: dict | None = None):
    db.add(
        AdminAuditLog(
            entity=entity,
            entity_id=entity_id,
            action=action,
            payload=json.dumps(payload or {}, ensure_ascii=False),
        )
    )
