"""
Everything about tracking already-approved actions: listing them for the
dashboard, updating their status, and the daily deadline scan that flags
anything overdue.
"""
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.auth import get_current_user, require_role
from app.services.audit import write_audit

router = APIRouter(prefix="/api/v1/actions", tags=["actions"])

# Auditors are read-only by definition (PRD persona 4) — everyone else who
# can see an action is allowed to move it through its lifecycle.
STATUS_UPDATE_ROLES = ["legal_officer", "admin_authority", "department_officer"]


@router.get("", response_model=list[schemas.ActionOut])
def list_actions(
    status: str | None = None,
    department_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    q = db.query(models.Action)
    if status:
        q = q.filter(models.Action.status == status)
    if department_id:
        q = q.filter(models.Action.assigned_department_id == department_id)
    return q.order_by(models.Action.deadline_date.asc()).all()


@router.patch("/{action_id}/status", response_model=schemas.ActionOut)
def update_action_status(
    action_id: str,
    body: schemas.ActionStatusUpdateIn,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(STATUS_UPDATE_ROLES)),
):
    action = db.query(models.Action).filter(models.Action.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    if body.status not in ("pending", "in_progress", "completed"):
        raise HTTPException(status_code=400, detail="Status must be pending, in_progress, or completed")

    action.status = body.status
    if body.notes:
        action.notes = body.notes
    if body.status == "completed":
        from datetime import datetime
        action.completed_at = datetime.utcnow()

    write_audit(db, "action", action.id, f"Status changed to {body.status}", actor_id=current_user.id)
    db.commit()
    db.refresh(action)
    return action


@router.get("/dashboard/stats")
def dashboard_stats(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Powers the four summary cards on the Actioned Dashboard."""
    total_cases = db.query(models.Case).count()
    all_actions = db.query(models.Action).all()
    open_actions = [a for a in all_actions if a.status != "completed"]
    overdue = [a for a in open_actions if a.deadline_date and a.deadline_date < date.today()]
    completed = [a for a in all_actions if a.status == "completed"]
    compliance_rate = round((len(completed) / len(all_actions)) * 100) if all_actions else 0

    return {
        "total_cases": total_cases,
        "open_directives": len(open_actions),
        "overdue": len(overdue),
        "compliance_rate": compliance_rate,
    }


def run_daily_deadline_scan(db: Session):
    """Meant to be triggered by a scheduled job (see README for how to wire up
    a cron / APScheduler trigger). Flags anything past its deadline as overdue
    and creates an Alert row — this is a SYSTEM action, never a user one."""
    overdue_actions = (
        db.query(models.Action)
        .filter(models.Action.status != "completed", models.Action.deadline_date < date.today())
        .all()
    )
    for action in overdue_actions:
        alert = models.Alert(action_id=action.id, alert_type="overdue")
        db.add(alert)
        write_audit(db, "action", action.id, "Marked overdue by scheduled deadline scan", actor_type="system")
    db.commit()
    return len(overdue_actions)
