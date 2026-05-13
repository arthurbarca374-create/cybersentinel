from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.models.schemas import UserPublic
from backend.models.user import User
from backend.services.auth import get_current_user
from backend.core.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserPublic)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/trial/status")
def trial_status(current_user: User = Depends(get_current_user)):
    return {
        "is_active": current_user.is_trial_active,
        "expires_at": current_user.trial_expires_at,
        "scans_used": current_user.trial_scans_used,
        "scans_remaining": current_user.trial_scans_remaining,
        "trial_days": settings.FREE_TRIAL_DAYS,
        "max_scans": settings.FREE_TRIAL_SCANS,
    }


@router.post("/trial/use-scan")
def use_scan(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_trial_active:
        raise HTTPException(status_code=403, detail="Trial expired")
    if current_user.trial_scans_remaining == 0:
        raise HTTPException(status_code=403, detail="No scans remaining")

    current_user.trial_scans_used += 1
    db.commit()
    return {
        "scans_remaining": current_user.trial_scans_remaining,
        "message": "Scan used successfully",
    }


@router.get("/community/members")
def community_members(db: Session = Depends(get_db)):
    """Public endpoint: return count and recent members (no private data)."""
    total = db.query(User).filter(User.is_active == True).count()
    recent = (
        db.query(User)
        .filter(User.is_active == True)
        .order_by(User.created_at.desc())
        .limit(12)
        .all()
    )
    return {
        "total_members": total,
        "recent_members": [
            {"username": u.username, "avatar_url": u.avatar_url, "joined": u.created_at}
            for u in recent
        ],
    }
