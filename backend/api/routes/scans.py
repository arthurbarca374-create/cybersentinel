import asyncio
import secrets
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.core.limiter import limiter
from backend.models.schemas import (
    TargetCreate, TargetResponse, ScanRequest, ScanResponse,
)
from backend.services.scan_engine import (
    get_scan_types, create_target, get_targets, delete_target,
    create_scan, get_scans, get_scan, get_findings, run_scan,
)
from backend.services.auth import get_current_user
from backend.models.user import User

router = APIRouter(prefix="/api/scans", tags=["scans"])


@router.get("/types")
def list_scan_types():
    return {"scan_types": get_scan_types()}


@router.post("/targets", response_model=TargetResponse, status_code=201)
def add_target(payload: TargetCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return create_target(db, current_user.id, payload.name, payload.host,
                         port=payload.port, os_info=payload.os_info,
                         notes=payload.notes, tags=payload.tags)


@router.get("/targets")
def list_targets(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_targets(db, current_user.id)


@router.delete("/targets/{target_id}")
def remove_target(target_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not delete_target(db, target_id, current_user.id):
        raise HTTPException(status_code=404, detail="Target not found")
    return {"detail": "Target removed"}


@router.post("/run", response_model=ScanResponse, status_code=201)
@limiter.limit("10/minute")
async def start_scan(request: Request, payload: ScanRequest,
                     db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user.is_trial_active:
        raise HTTPException(status_code=403, detail="Trial expired")
    if current_user.trial_scans_remaining <= 0:
        raise HTTPException(status_code=403, detail="No scans remaining")

    config = payload.config or {}
    if payload.ports:
        config["ports"] = payload.ports

    scan = create_scan(db, current_user.id, payload.target_id, payload.scan_type, config)
    asyncio.create_task(run_scan(scan.id))
    return scan


@router.get("")
def list_scans(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_scans(db, current_user.id)


@router.get("/{scan_id}", response_model=ScanResponse)
def get_scan_details(scan_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    scan = get_scan(db, scan_id, current_user.id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan


@router.get("/{scan_id}/findings")
def list_findings(scan_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    scan = get_scan(db, scan_id, current_user.id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return get_findings(db, scan_id)
