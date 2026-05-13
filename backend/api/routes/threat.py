from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.models.schemas import IntelQuery, ThreatIntelResponse, IntelReportCreate
from backend.services.threat_intel import (
    lookup_indicator, store_intel, get_threat_feed,
    get_threat_stats, create_intel_report, get_intel_reports,
)
from backend.services.auth import get_current_user
from backend.models.user import User

router = APIRouter(prefix="/api/threat", tags=["threat intelligence"])


@router.post("/lookup")
async def lookup(payload: IntelQuery, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    result = await lookup_indicator(payload.indicator, payload.indicator_type)
    store_intel(db, "lookup", payload.indicator, payload.indicator_type, result)
    return result


@router.get("/lookup/{indicator_type}/{indicator}")
async def lookup_by_path(indicator_type: str, indicator: str, db: Session = Depends(get_db),
                         current_user: User = Depends(get_current_user)):
    result = await lookup_indicator(indicator, indicator_type)
    store_intel(db, "lookup", indicator, indicator_type, result)
    return result


@router.get("/feed")
def threat_feed(limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    return get_threat_feed(db, limit)


@router.get("/stats")
def threat_stats(db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    return get_threat_stats(db)


@router.get("/reports")
def list_reports(db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    return get_intel_reports(db)


@router.post("/reports", status_code=201)
def create_report(payload: IntelReportCreate, db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    report = create_intel_report(db, current_user.id, payload.title,
                                  summary=payload.summary,
                                  indicators=payload.indicators,
                                  mitre_techniques=payload.mitre_techniques,
                                  tlp=payload.tlp)
    return report
