from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_db
from .models import AdminAuditLog

router = APIRouter(prefix="/admin/audit", tags=["admin-audit"])


@router.get("")
def list_audit(limit: int = 100, db: Session = Depends(get_db)):
    stmt = select(AdminAuditLog).order_by(AdminAuditLog.created_at.desc()).limit(min(500, max(1, limit)))
    rows = list(db.execute(stmt).scalars().all())
    return [
        {
            "id": r.id,
            "entity": r.entity,
            "entity_id": r.entity_id,
            "action": r.action,
            "payload": r.payload,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
