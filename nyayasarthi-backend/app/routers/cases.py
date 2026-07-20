"""
Handles: uploading a judgment PDF, running it through OCR + Gemini, and saving
the draft directives to the database as pending_verification.
"""
import hashlib
import os
import shutil
import uuid
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.services.extraction import extract_text_from_pdf, run_ai_extraction, compute_deadline
from app.services.audit import write_audit

router = APIRouter(prefix="/api/v1/cases", tags=["cases"])

UPLOAD_DIR = "uploaded_judgments"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=schemas.CaseOut)
def upload_judgment(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # 1. Save the file and hash it, so we can detect duplicate uploads
    file_bytes = file.file.read()
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    existing = db.query(models.Case).filter(models.Case.source_pdf_hash == file_hash).first()
    if existing:
        if existing.status == "extraction_failed" or existing.case_number == "Pending extraction…":
            # A previous attempt on this exact file never completed — clean it up
            # and let this upload retry from scratch, instead of blocking it forever.
            db.query(models.Directive).filter(models.Directive.case_id == existing.id).delete()
            db.delete(existing)
            db.commit()
        else:
            raise HTTPException(
                status_code=409,
                detail=f"This judgment appears to already be in the system as case {existing.case_number}."
            )

    file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{file.filename}")
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    # 2. Create the case record immediately so the user sees progress
    case = models.Case(
        case_number="Pending extraction…",
        source_pdf_url=file_path,
        source_pdf_hash=file_hash,
        status="extracting",
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    write_audit(db, "case", case.id, "Judgment PDF uploaded", actor_type="human")
    db.commit()

    # 3. Extract text (OCR if needed)
    try:
        text, doc_type = extract_text_from_pdf(file_path)
        case.document_type = doc_type
    except Exception as e:
        case.status = "extraction_failed"
        db.commit()
        write_audit(db, "case", case.id, f"Text extraction failed: {e}", actor_type="system")
        db.commit()
        raise HTTPException(status_code=500, detail=f"Could not read the PDF: {e}")

    # 4. Run Gemini extraction
    try:
        result = run_ai_extraction(text)
    except ValueError as e:
        case.status = "extraction_failed"
        db.commit()
        write_audit(db, "case", case.id, f"AI extraction failed: {e}", actor_type="system")
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))

    # 5. Save case metadata + directives as DRAFT (pending_verification) — never auto-approved
    case.case_number = result.get("case_number") or "Unknown case number"
    case.court_name = result.get("court_name")
    case.parties = {"petitioner": result.get("petitioner"), "respondent": result.get("respondent")}
    if result.get("order_date"):
        try:
            case.order_date = result["order_date"]
        except Exception:
            pass
    case.status = "pending_verification"
    db.commit()

    departments = {d.name: d.id for d in db.query(models.Department).all()}

    for d in result.get("directives", []):
        deadline_date = compute_deadline(result.get("order_date", ""), d.get("deadline_expression_raw", ""))
        directive = models.Directive(
            case_id=case.id,
            raw_description=d.get("raw_description", ""),
            source_page=d.get("source_page"),
            source_snippet=d.get("source_snippet"),
            ai_confidence=d.get("ai_confidence", "medium"),
            deadline_expression_raw=d.get("deadline_expression_raw"),
            deadline_date_computed=deadline_date,
            suggested_department_id=departments.get(d.get("suggested_department")),
            verification_status="pending_verification",
        )
        db.add(directive)

    db.commit()
    write_audit(db, "case", case.id, f"AI extraction complete — {len(result.get('directives', []))} directive(s) identified", actor_type="system")
    db.commit()

    db.refresh(case)
    return case


@router.get("/{case_id}", response_model=schemas.CaseOut)
def get_case(case_id: str, db: Session = Depends(get_db)):
    case = db.query(models.Case).filter(models.Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.get("", response_model=list[schemas.CaseOut])
def list_cases(status: str | None = None, db: Session = Depends(get_db)):
    q = db.query(models.Case)
    if status:
        q = q.filter(models.Case.status == status)
    return q.order_by(models.Case.created_at.desc()).all()
