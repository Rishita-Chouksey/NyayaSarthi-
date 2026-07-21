"""
Core authentication utilities: password hashing, JWT creation/verification,
and the FastAPI dependencies that protect routes and enforce role-based
access control.

Every protected endpoint in NyayaSarthi should depend on `get_current_user`
(or the stricter `require_role([...])`) from this file — never re-implement
token checking inside an individual router.
"""
import os
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.database import get_db
from app import models

JWT_SECRET = os.getenv("JWT_SECRET", "change-this-to-a-long-random-string")
JWT_ALGORITHM = "HS256"
# Government officials shouldn't have to re-authenticate every day; a week is
# a reasonable balance between convenience and session hygiene for an MVP.
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# auto_error=False so we can raise our own clear 401 instead of FastAPI's
# generic "Not authenticated" when the header is missing entirely.
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def create_access_token(user: "models.User") -> str:
    payload = {
        "sub": user.id,
        "role": user.role,
        "email": user.email,
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Your session has expired or is invalid — please log in again.",
        )


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> "models.User":
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_access_token(credentials.credentials)
    user = db.query(models.User).filter(models.User.id == payload.get("sub")).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Account not found or has been deactivated")
    return user


def require_role(allowed_roles: List[str]):
    """
    FastAPI dependency factory for RBAC. Usage:
        @router.post(..., dependencies=[Depends(require_role(["legal_officer","admin_authority"]))])
    or, if you also need the user object inside the route:
        current_user: models.User = Depends(require_role(["legal_officer"]))
    """
    def _check(user: "models.User" = Depends(get_current_user)) -> "models.User":
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="Your role does not have permission to perform this action.",
            )
        return user
    return _check
