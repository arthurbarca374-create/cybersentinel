import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from backend.models.api_key import ApiKey
from backend.models.user import User


def generate_api_key() -> tuple[str, str, str]:
    key = f"cs_{secrets.token_hex(32)}"
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    key_prefix = key[:12]
    return key, key_hash, key_prefix


def create_api_key(db: Session, user_id: int, name: str, expires_in_days: Optional[int] = None) -> tuple[ApiKey, str]:
    key, key_hash, key_prefix = generate_api_key()
    api_key = ApiKey(
        user_id=user_id,
        name=name,
        key_prefix=key_prefix,
        key_hash=key_hash,
        expires_at=datetime.utcnow() + timedelta(days=expires_in_days) if expires_in_days else None,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    return api_key, key


def get_user_api_keys(db: Session, user_id: int) -> list[ApiKey]:
    return db.query(ApiKey).filter(
        ApiKey.user_id == user_id,
        ApiKey.is_active == True,
    ).all()


def revoke_api_key(db: Session, key_id: int, user_id: int) -> bool:
    api_key = db.query(ApiKey).filter(
        ApiKey.id == key_id,
        ApiKey.user_id == user_id,
    ).first()
    if not api_key:
        return False
    api_key.is_active = False
    db.commit()
    return True


def authenticate_api_key(db: Session, key: str) -> Optional[User]:
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    api_key = db.query(ApiKey).filter(
        ApiKey.key_hash == key_hash,
        ApiKey.is_active == True,
    ).first()
    if not api_key:
        return None
    if api_key.expires_at and api_key.expires_at < datetime.utcnow():
        return None
    api_key.last_used_at = datetime.utcnow()
    db.commit()
    return db.query(User).filter(User.id == api_key.user_id).first()
