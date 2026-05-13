from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, Float, ForeignKey, JSON
from sqlalchemy.sql import func
from backend.db.database import Base


class ThreatIntel(Base):
    __tablename__ = "threat_intel"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, nullable=False, index=True)
    indicator = Column(String, nullable=False, index=True)
    indicator_type = Column(String, nullable=False)
    severity = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    raw_data = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)
    first_seen = Column(DateTime, nullable=True)
    last_seen = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class IntelReport(Base):
    __tablename__ = "intel_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    indicators = Column(JSON, nullable=True)
    mitre_techniques = Column(JSON, nullable=True)
    tlp = Column(String, default="CLEAR")
    status = Column(String, default="draft")
    pdf_path = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
