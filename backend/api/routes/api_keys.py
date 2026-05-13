from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional
from backend.db.database import get_db
from backend.models.schemas import ApiKeyCreate
from backend.services.api_keys import create_api_key, get_user_api_keys, revoke_api_key
from backend.services.auth import get_current_user
from backend.models.user import User

router = APIRouter(prefix="/api/keys", tags=["API keys"])


@router.post("", status_code=201)
def create_key(payload: ApiKeyCreate, db: Session = Depends(get_db),
               current_user: User = Depends(get_current_user)):
    api_key, raw_key = create_api_key(db, current_user.id, payload.name, payload.expires_in_days)
    return {
        "id": api_key.id,
        "name": api_key.name,
        "key_prefix": api_key.key_prefix,
        "key": raw_key,
        "expires_at": api_key.expires_at,
        "created_at": api_key.created_at,
    }


@router.get("")
def list_keys(db: Session = Depends(get_db),
              current_user: User = Depends(get_current_user)):
    keys = get_user_api_keys(db, current_user.id)
    return [{"id": k.id, "name": k.name, "key_prefix": k.key_prefix,
             "created_at": k.created_at, "last_used_at": k.last_used_at} for k in keys]


@router.delete("/{key_id}")
def revoke_key(key_id: int, db: Session = Depends(get_db),
               current_user: User = Depends(get_current_user)):
    if not revoke_api_key(db, key_id, current_user.id):
        raise HTTPException(status_code=404, detail="API key not found")
    return {"detail": "API key revoked"}
