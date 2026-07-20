"""
Every single action that changes data in NyayaSarthi must call write_audit()
in the SAME database transaction as the change itself. This is what guarantees
the audit trail can never drift from what actually happened — the core
accountability promise of the whole product.
"""
from sqlalchemy.orm import Session
from app.models import AuditLog


def write_audit(db: Session, entity_type: str, entity_id: str, event_type: str,
                 actor_id: str | None = None, actor_type: str = "human",
                 before_state: dict | None = None, after_state: dict | None = None):
    entry = AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        event_type=event_type,
        actor_id=actor_id,
        actor_type=actor_type,
        before_state=before_state,
        after_state=after_state,
    )
    db.add(entry)
    # Deliberately no db.commit() here — the caller commits once, together with
    # the actual data change, so the two can never end up out of sync.
