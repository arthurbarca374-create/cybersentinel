from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.models.schemas import AnalysisRequest, AnalysisResponse
from backend.services.ai_analysis import analyze_scan
from backend.services.scan_engine import get_scan
from backend.services.auth import get_current_user
from backend.models.user import User

router = APIRouter(prefix="/api/ai", tags=["AI analysis"])


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(payload: AnalysisRequest, db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    scan = get_scan(db, payload.scan_id, current_user.id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    if scan.status != "completed":
        raise HTTPException(status_code=400, detail="Scan is not completed yet")

    result = await analyze_scan(db, payload.scan_id, payload.model)
    return result


@router.get("/models")
def list_models():
    return {
        "models": [
            {"id": "default", "name": "Local analysis (no API key required)"},
            {"id": "claude", "name": "Claude 3 Haiku (Anthropic)"},
            {"id": "gpt4", "name": "GPT-4o Mini (OpenAI)"},
        ]
    }
