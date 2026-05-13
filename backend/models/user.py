from datetime import datetime, timedelta

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from backend.db.database import Base
from backend.core.config import get_settings

settings = get_settings()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    github_id = Column(String, unique=True, index=True, nullable=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=True)  # null for OAuth-only users
    avatar_url = Column(String, nullable=True)
    bio = Column(Text, nullable=True)

    # Account state
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)

    # Free trial tracking
    trial_started_at = Column(DateTime, nullable=True)
    trial_scans_used = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime, nullable=True)

    @property
    def trial_expires_at(self):
        if self.trial_started_at is None:
            return None
        return self.trial_started_at + timedelta(days=settings.FREE_TRIAL_DAYS)

    @property
    def is_trial_active(self):
        if self.trial_expires_at is None:
            return False
        return datetime.utcnow() < self.trial_expires_at

    @property
    def trial_scans_remaining(self):
        return max(0, settings.FREE_TRIAL_SCANS - self.trial_scans_used)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=True)
    action = Column(String, nullable=False)
    detail = Column(Text, nullable=True)
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
