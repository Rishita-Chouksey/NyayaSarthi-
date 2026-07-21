"""
Signup, login (email/password), and "Sign in with Google" — the three ways
a government official can get into NyayaSarthi. All three converge on the
same JWT, so the rest of the API never needs to know how the user
authenticated; it only ever sees `get_current_user`.

Design choices worth knowing:
- Every account is issued with an explicit role at signup (there is no
  "unassigned" account for the manual-signup path) so RBAC is meaningful
  from the first request.
- A brand-new Google sign-in is provisioned with the lowest-privilege role
  (department_officer) by default, since Google alone can't prove which
  government role someone actually holds. An admin_authority can promote
  the account afterwards via the /departments or a future /users endpoint.
- Login, signup, and every Google sign-in are all written to the audit log,
  matching the "who did what, when" requirement in the Backend Schema doc.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.auth import create_access_token, get_current_user, hash_password, verify_password
from app.services.audit import write_audit
from app.services.google_auth import verify_google_token

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

ALLOWED_SIGNUP_ROLES = ["legal_officer", "admin_authority", "department_officer", "auditor"]


@router.post("/signup", response_model=schemas.LoginOut)
def signup(body: schemas.SignupIn, db: Session = Depends(get_db)):
    email = body.email.strip().lower()

    if body.role not in ALLOWED_SIGNUP_ROLES:
        raise HTTPException(status_code=400, detail=f"role must be one of {ALLOWED_SIGNUP_ROLES}")
    if len(body.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    existing = db.query(models.User).filter(models.User.email == email).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail="An account with this official email already exists — please log in instead.",
        )

    if body.department_id:
        dept = db.query(models.Department).filter(models.Department.id == body.department_id).first()
        if not dept:
            raise HTTPException(status_code=400, detail="Selected department was not found")

    user = models.User(
        full_name=body.full_name.strip(),
        email=email,
        password_hash=hash_password(body.password),
        role=body.role,
        department_id=body.department_id,
        auth_provider="local",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    write_audit(db, "user", user.id, "Account created (manual signup)", actor_id=user.id, actor_type="human")
    db.commit()

    token = create_access_token(user)
    return schemas.LoginOut(access_token=token, role=user.role, full_name=user.full_name)


@router.post("/login", response_model=schemas.LoginOut)
def login(body: schemas.LoginIn, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    user = db.query(models.User).filter(models.User.email == email).first()

    invalid_credentials = (
        not user
        or user.auth_provider != "local"
        or not user.password_hash
        or not verify_password(body.password, user.password_hash)
    )
    if invalid_credentials:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="This account has been deactivated. Contact your admin authority.")

    write_audit(db, "user", user.id, "Logged in", actor_id=user.id, actor_type="human")
    db.commit()

    token = create_access_token(user)
    return schemas.LoginOut(access_token=token, role=user.role, full_name=user.full_name)


@router.post("/google", response_model=schemas.LoginOut)
def google_login(body: schemas.GoogleAuthIn, db: Session = Depends(get_db)):
    try:
        payload = verify_google_token(body.credential)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    email = payload["email"].strip().lower()
    google_sub = payload["sub"]
    user = db.query(models.User).filter(models.User.email == email).first()

    if user is None:
        user = models.User(
            full_name=payload.get("name") or email.split("@")[0],
            email=email,
            password_hash=None,
            role="department_officer",  # least-privilege default; promote via admin
            auth_provider="google",
            google_sub=google_sub,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        write_audit(db, "user", user.id, "Account created (Google sign-in)", actor_id=user.id, actor_type="human")
        db.commit()
    elif not user.google_sub:
        # Existing account with this email (created manually) — link Google
        # as an additional sign-in method instead of creating a duplicate user.
        user.google_sub = google_sub
        db.commit()

    if not user.is_active:
        raise HTTPException(status_code=403, detail="This account has been deactivated. Contact your admin authority.")

    write_audit(db, "user", user.id, "Logged in via Google", actor_id=user.id, actor_type="human")
    db.commit()

    token = create_access_token(user)
    return schemas.LoginOut(access_token=token, role=user.role, full_name=user.full_name)


@router.get("/me", response_model=schemas.UserOut)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user
