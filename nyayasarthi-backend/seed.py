"""
Run this once after setting up the database, to populate the default
department list the AI extraction routes suggestions into.

Command: python seed.py
"""
from app.database import SessionLocal, Base, engine
from app import models

Base.metadata.create_all(bind=engine)

DEFAULT_DEPARTMENTS = [
    ("Revenue Department", "REV"),
    ("District Registrar Office", "DRO"),
    ("Public Works Department", "PWD"),
    ("Home Department", "HOME"),
    ("Forest & Environment Dept.", "FOREST"),
    ("Municipal Corporation", "MUNI"),
]

db = SessionLocal()
for name, code in DEFAULT_DEPARTMENTS:
    exists = db.query(models.Department).filter(models.Department.code == code).first()
    if not exists:
        db.add(models.Department(name=name, code=code))
db.commit()
db.close()
print(f"Seeded {len(DEFAULT_DEPARTMENTS)} departments.")
