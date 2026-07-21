from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import models

router = APIRouter(prefix="/api/v1/departments", tags=["departments"])

# Intentionally left public (no auth dependency): the signup screen needs the
# department list before a new official has an account, and this data isn't
# sensitive on its own (just names/codes, no case data).


@router.get("")
def list_departments(db: Session = Depends(get_db)):
    depts = db.query(models.Department).all()
    return [{"id": d.id, "name": d.name, "code": d.code} for d in depts]
