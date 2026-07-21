"""
Run this once after setting up the database, to populate the default
department list the AI extraction routes suggestions into.

Command: python seed.py
"""
from app.auth import hash_password
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

# One demo login per role so the team can try every screen immediately on a
# shared DB, without waiting on the signup flow. Change these passwords (or
# delete these rows) before any real deployment.
DEMO_USERS = [
    ("Priya Sharma", "priya.legal@nyayasarthi.test", "legal_officer", "demo-pass-123"),
    ("Rakesh Verma", "rakesh.admin@nyayasarthi.test", "admin_authority", "demo-pass-123"),
    ("Sunita Rao", "sunita.dept@nyayasarthi.test", "department_officer", "demo-pass-123"),
    ("Anil Mehta", "anil.audit@nyayasarthi.test", "auditor", "demo-pass-123"),
]

db = SessionLocal()

for name, code in DEFAULT_DEPARTMENTS:
    exists = db.query(models.Department).filter(models.Department.code == code).first()
    if not exists:
        db.add(models.Department(name=name, code=code))
db.commit()

for full_name, email, role, password in DEMO_USERS:
    exists = db.query(models.User).filter(models.User.email == email).first()
    if not exists:
        db.add(models.User(
            full_name=full_name,
            email=email,
            password_hash=hash_password(password),
            role=role,
            auth_provider="local",
        ))
db.commit()
db.close()

print(f"Seeded {len(DEFAULT_DEPARTMENTS)} departments.")
print(f"Seeded {len(DEMO_USERS)} demo users (password for all: demo-pass-123):")
for full_name, email, role, _ in DEMO_USERS:
    print(f"  - {email}  [{role}]")
