from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from backend.db.database import get_db
from backend.models.schemas import BlockchainQuery, BlockchainAnalysisResponse, RecoveryRequest
from backend.services.blockchain import (
    analyze_address, store_analysis, get_recent_analyses,
    create_recovery, get_recoveries,
)
from backend.services.auth import get_current_user
from backend.models.user import User

router = APIRouter(prefix="/api/blockchain", tags=["blockchain"])


@router.post("/analyze")
async def analyze(payload: BlockchainQuery, db: Session = Depends(get_db),
                  current_user: Optional[User] = Depends(get_current_user)):
    analysis = await analyze_address(payload.chain, payload.address)
    if current_user:
        store_analysis(db, current_user.id, payload.chain, payload.address, analysis)
    return analysis


@router.get("/analyze/{chain}/{address}")
async def analyze_by_path(chain: str, address: str, db: Session = Depends(get_db),
                          current_user: Optional[User] = Depends(get_current_user)):
    analysis = await analyze_address(chain, address)
    if current_user and analysis.get("valid_format"):
        store_analysis(db, current_user.id, chain, address, analysis)
    return analysis


@router.get("/analyses")
def list_analyses(db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    return get_recent_analyses(db, user_id=current_user.id)


@router.post("/recover", status_code=201)
def start_recovery(payload: RecoveryRequest, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    recovery = create_recovery(db, current_user.id, payload.chain, payload.method)
    return recovery


@router.get("/recoveries")
def list_recoveries(db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    return get_recoveries(db, user_id=current_user.id)
