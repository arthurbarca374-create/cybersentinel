from datetime import datetime
from typing import Optional
from sqlalchemy import Column, DateTime, Integer, String, Text, Float, JSON, ForeignKey
from sqlalchemy.sql import func
from backend.db.database import Base


class BlockchainAnalysis(Base):
    __tablename__ = "blockchain_analysis"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    chain = Column(String, nullable=False)
    address = Column(String, nullable=False)
    analysis_type = Column(String, nullable=False)
    balance = Column(String, nullable=True)
    transaction_count = Column(Integer, nullable=True)
    risk_score = Column(Float, nullable=True)
    tags = Column(JSON, nullable=True)
    report = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class WalletRecovery(Base):
    __tablename__ = "wallet_recoveries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    chain = Column(String, nullable=False)
    status = Column(String, default="pending")
    method = Column(String, nullable=True)
    progress = Column(Float, default=0.0)
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
