from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import models

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


@router.get("/{entity_type}/{entity_id}")
def get_audit_history(entity_type: str, entity_id: str, db: Session = Depends(get_db)):
    """Full chronological history for any case, directive, or action — read-only,
    nothing in the system ever deletes or edits these rows."""
    entries = (
        db.query(models.AuditLog)
        .filter(models.AuditLog.entity_type == entity_type, models.AuditLog.entity_id == entity_id)
        .order_by(models.AuditLog.created_at.asc())
        .all()
    )
    return [
        {
            "event": e.event_type,
            "actor_type": e.actor_type,
            "at": e.created_at.isoformat(),
        }
        for e in entries
    ]
