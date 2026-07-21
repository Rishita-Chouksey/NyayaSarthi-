"""
The human-in-the-loop layer. A directive can only ever become a real, tracked
Action through one of these three endpoints — and approve/edit are the ONLY
paths that create an Action row. Nothing here runs automatically.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.auth import require_role
from app.services.audit import write_audit

router = APIRouter(prefix="/api/v1/verification", tags=["verification"])

# Only the two personas the PRD assigns this responsibility to may
# approve/edit/reject a directive — everyone else can still view case data.
REVIEWER_ROLES = ["legal_officer", "admin_authority"]


def _maybe_close_case(db: Session, case: models.Case):
    directives = db.query(models.Directive).filter(models.Directive.case_id == case.id).all()
    if directives and all(d.verification_status != "pending_verification" for d in directives):
        case.status = "actioned"
    else:
        case.status = "verification_in_progress"


@router.post("/{directive_id}/approve", response_model=schemas.ActionOut)
def approve_directive(
    directive_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(REVIEWER_ROLES)),
):
    directive = db.query(models.Directive).filter(models.Directive.id == directive_id).first()
    if not directive:
        raise HTTPException(status_code=404, detail="Directive not found")
    if directive.verification_status != "pending_verification":
        raise HTTPException(status_code=400, detail="This directive has already been reviewed")

    directive.verification_status = "approved"
    directive.verified_by = current_user.id
    directive.verified_at = datetime.utcnow()

    action = models.Action(
        directive_id=directive.id,
        case_id=directive.case_id,
        description=directive.raw_description,
        assigned_department_id=directive.suggested_department_id,
        deadline_date=directive.deadline_date_computed,
        status="pending",
    )
    db.add(action)

    case = db.query(models.Case).filter(models.Case.id == directive.case_id).first()
    _maybe_close_case(db, case)

    write_audit(db, "directive", directive.id, "Directive approved", actor_id=current_user.id)
    db.commit()
    db.refresh(action)
    return action


@router.post("/{directive_id}/edit-approve", response_model=schemas.ActionOut)
def edit_and_approve_directive(
    directive_id: str,
    edits: schemas.EditApproveDirectiveIn,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(REVIEWER_ROLES)),
):
    directive = db.query(models.Directive).filter(models.Directive.id == directive_id).first()
    if not directive:
        raise HTTPException(status_code=404, detail="Directive not found")
    if directive.verification_status != "pending_verification":
        raise HTTPException(status_code=400, detail="This directive has already been reviewed")

    if edits.raw_description is not None:
        directive.raw_description = edits.raw_description
    if edits.suggested_department_id is not None:
        directive.suggested_department_id = edits.suggested_department_id
    if edits.deadline_date_computed is not None:
        directive.deadline_date_computed = edits.deadline_date_computed

    directive.verification_status = "edited_approved"
    directive.verified_by = current_user.id
    directive.verified_at = datetime.utcnow()

    action = models.Action(
        directive_id=directive.id,
        case_id=directive.case_id,
        description=directive.raw_description,
        assigned_department_id=directive.suggested_department_id,
        deadline_date=directive.deadline_date_computed,
        status="pending",
    )
    db.add(action)

    case = db.query(models.Case).filter(models.Case.id == directive.case_id).first()
    _maybe_close_case(db, case)

    write_audit(db, "directive", directive.id, "Directive edited and approved", actor_id=current_user.id)
    db.commit()
    db.refresh(action)
    return action


@router.post("/{directive_id}/reject")
def reject_directive(
    directive_id: str,
    body: schemas.RejectDirectiveIn,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(REVIEWER_ROLES)),
):
    directive = db.query(models.Directive).filter(models.Directive.id == directive_id).first()
    if not directive:
        raise HTTPException(status_code=404, detail="Directive not found")
    if directive.verification_status != "pending_verification":
        raise HTTPException(status_code=400, detail="This directive has already been reviewed")

    directive.verification_status = "rejected"
    directive.rejection_reason = body.reason
    directive.verified_by = current_user.id
    directive.verified_at = datetime.utcnow()

    case = db.query(models.Case).filter(models.Case.id == directive.case_id).first()
    _maybe_close_case(db, case)

    write_audit(db, "directive", directive.id, f"Directive rejected: {body.reason}", actor_id=current_user.id)
    db.commit()
    return {"status": "rejected", "directive_id": directive_id}
