"""
This file defines the database tables as Python classes.
Each class below becomes one table in PostgreSQL — this is the direct implementation
of the Backend Schema document (1_NyayaSarthi_PRD.md's companion, 5_NyayaSarthi_Backend_Schema.md).
"""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Date, DateTime, ForeignKey, Enum, Boolean, Integer
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    full_name = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    # Nullable because Google-only accounts never set a local password.
    password_hash = Column(String(255), nullable=True)
    role = Column(Enum("legal_officer", "admin_authority", "department_officer", "auditor", name="user_role"), nullable=False)
    department_id = Column(UUID(as_uuid=False), ForeignKey("departments.id"), nullable=True)
    # How this account authenticates. "google" accounts sign in exclusively via
    # Google OAuth; "local" accounts use email + password. An account can gain
    # a google_sub later (linked) without changing its original auth_provider.
    auth_provider = Column(Enum("local", "google", name="auth_provider"), default="local", nullable=False)
    google_sub = Column(String(255), unique=True, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    department = relationship("Department", back_populates="users")


class Department(Base):
    __tablename__ = "departments"
    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name = Column(String(150), nullable=False)
    code = Column(String(30), unique=True, nullable=False)
    parent_department_id = Column(UUID(as_uuid=False), ForeignKey("departments.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="department")


class Case(Base):
    __tablename__ = "cases"
    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    case_number = Column(String(100), nullable=False)
    court_name = Column(String(200))
    order_date = Column(Date)
    parties = Column(JSONB)  # {"petitioner": "...", "respondent": "..."}
    source_pdf_url = Column(Text)
    source_pdf_hash = Column(String(64), index=True)
    document_type = Column(Enum("digital", "scanned", name="document_type"))
    status = Column(
        Enum("uploaded", "extracting", "pending_verification", "verification_in_progress",
             "actioned", "extraction_failed", name="case_status"),
        default="uploaded",
    )
    uploaded_by = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    directives = relationship("Directive", back_populates="case", cascade="all, delete-orphan")


class Directive(Base):
    __tablename__ = "directives"
    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    case_id = Column(UUID(as_uuid=False), ForeignKey("cases.id"), nullable=False)
    raw_description = Column(Text, nullable=False)
    source_page = Column(Integer)
    source_snippet = Column(Text)
    ai_confidence = Column(Enum("high", "medium", "low", name="confidence_level"))
    deadline_expression_raw = Column(String(255))
    deadline_date_computed = Column(Date)
    suggested_department_id = Column(UUID(as_uuid=False), ForeignKey("departments.id"), nullable=True)
    verification_status = Column(
        Enum("pending_verification", "approved", "edited_approved", "rejected", name="verification_status"),
        default="pending_verification",
    )
    rejection_reason = Column(Text, nullable=True)
    verified_by = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    case = relationship("Case", back_populates="directives")
    action = relationship("Action", back_populates="directive", uselist=False, cascade="all, delete-orphan")


class Action(Base):
    __tablename__ = "actions"
    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    directive_id = Column(UUID(as_uuid=False), ForeignKey("directives.id"), unique=True, nullable=False)
    case_id = Column(UUID(as_uuid=False), ForeignKey("cases.id"), nullable=False)
    description = Column(Text, nullable=False)
    assigned_department_id = Column(UUID(as_uuid=False), ForeignKey("departments.id"), nullable=True)
    assigned_user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)
    deadline_date = Column(Date)
    status = Column(Enum("pending", "in_progress", "completed", "overdue", name="action_status"), default="pending")
    completed_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    directive = relationship("Directive", back_populates="action")


class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    entity_type = Column(Enum("case", "directive", "action", "user", name="audit_entity_type"), nullable=False)
    entity_id = Column(UUID(as_uuid=False), nullable=False)
    event_type = Column(String(50), nullable=False)
    actor_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)
    actor_type = Column(Enum("human", "system", name="actor_type"), default="human")
    before_state = Column(JSONB, nullable=True)
    after_state = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class Alert(Base):
    __tablename__ = "alerts"
    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    action_id = Column(UUID(as_uuid=False), ForeignKey("actions.id"), nullable=False)
    alert_type = Column(Enum("approaching", "overdue", name="alert_type"), nullable=False)
    triggered_at = Column(DateTime, default=datetime.utcnow)
    acknowledged_by = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
