from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserPublic(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    is_trial_active: bool
    trial_scans_remaining: int
    trial_expires_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class LoginRequest(BaseModel):
    username: str
    password: str


# ── Scan Engine ────────────────────────────────────────────

class TargetCreate(BaseModel):
    name: str
    host: str
    port: Optional[int] = None
    os_info: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[dict] = None


class TargetResponse(BaseModel):
    id: int
    name: str
    host: str
    port: Optional[int] = None
    os_info: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[dict] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ScanRequest(BaseModel):
    target_id: int
    scan_type: str = "quick"
    ports: Optional[str] = None
    config: Optional[dict] = None


class ScanResponse(BaseModel):
    id: int
    target_id: Optional[int]
    scan_type: str
    status: str
    progress: float
    result_summary: Optional[dict] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class FindingResponse(BaseModel):
    id: int
    scan_id: int
    type: str
    severity: str
    title: str
    description: Optional[str] = None
    recommendation: Optional[str] = None
    cve_id: Optional[str] = None
    cvss_score: Optional[float] = None
    port: Optional[int] = None
    evidence: Optional[dict] = None
    is_false_positive: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ScanScheduleCreate(BaseModel):
    target_id: int
    scan_type: str = "quick"
    cron_expression: str
    config: Optional[dict] = None


class ScanScheduleResponse(BaseModel):
    id: int
    target_id: int
    scan_type: str
    cron_expression: str
    is_active: bool
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Team / Org ─────────────────────────────────────────────

class OrgCreate(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None


class OrgResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    owner_id: int
    is_verified: bool
    max_members: int
    member_count: Optional[int] = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class TeamCreate(BaseModel):
    org_id: int
    name: str
    description: Optional[str] = None


class TeamResponse(BaseModel):
    id: int
    org_id: int
    name: str
    description: Optional[str] = None
    member_count: Optional[int] = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class InviteCreate(BaseModel):
    org_id: int
    email: str
    role: str = "member"


class MemberResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    role: str
    joined_at: datetime

    model_config = {"from_attributes": True}


# ── Threat Intel ───────────────────────────────────────────

class IntelQuery(BaseModel):
    indicator: str
    indicator_type: str = "ip"


class ThreatIntelResponse(BaseModel):
    id: int
    source: str
    indicator: str
    indicator_type: str
    severity: Optional[str] = None
    confidence: Optional[float] = None
    description: Optional[str] = None
    tags: Optional[dict] = None
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None

    model_config = {"from_attributes": True}


class IntelReportCreate(BaseModel):
    title: str
    summary: Optional[str] = None
    indicators: Optional[list] = None
    mitre_techniques: Optional[list] = None
    tlp: str = "CLEAR"


# ── AI Analysis ────────────────────────────────────────────

class AnalysisRequest(BaseModel):
    scan_id: int
    prompt: Optional[str] = None
    model: str = "default"


class AnalysisResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    scan_id: int
    analysis: str
    model_used: str
    findings_summary: Optional[dict] = None
    recommendations: Optional[list] = None


# ── Blockchain ─────────────────────────────────────────────

class BlockchainQuery(BaseModel):
    chain: str = "bitcoin"
    address: str


class BlockchainAnalysisResponse(BaseModel):
    id: int
    chain: str
    address: str
    analysis_type: str
    balance: Optional[str] = None
    transaction_count: Optional[int] = None
    risk_score: Optional[float] = None
    tags: Optional[dict] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RecoveryRequest(BaseModel):
    chain: str
    method: str = "mnemonic"
    data: Optional[dict] = None


# ── API Keys ───────────────────────────────────────────────

class ApiKeyCreate(BaseModel):
    name: str
    expires_in_days: Optional[int] = None
