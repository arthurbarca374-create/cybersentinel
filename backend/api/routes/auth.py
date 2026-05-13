import asyncio
import secrets
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from backend.core.security import create_access_token
from backend.db.database import get_db
from backend.models.schemas import LoginRequest, TokenResponse, UserCreate, UserPublic
from backend.services.auth import authenticate_user, get_current_user, register_user
from backend.services.github_oauth import (
    create_user_jwt,
    exchange_code_for_token,
    get_github_auth_url,
    get_github_user,
    upsert_github_user,
)
from backend.core.config import get_settings
from backend.core.limiter import limiter

settings = get_settings()
router = APIRouter(prefix="/api/auth", tags=["auth"])

_oauth_states: set = set()


@router.post("/register", response_model=TokenResponse, status_code=201)
@limiter.limit("5/minute")
def register(request: Request, payload: UserCreate, db: Session = Depends(get_db)):
    user = register_user(db, payload.username, payload.email, payload.password)
    token = create_access_token({"sub": str(user.id), "username": user.username})
    return {"access_token": token, "user": user}


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    user.last_login = datetime.utcnow()
    db.commit()
    token = create_access_token({"sub": str(user.id), "username": user.username})
    return {"access_token": token, "user": user}


@router.get("/github")
def github_login():
    state = secrets.token_urlsafe(32)
    _oauth_states.add(state)
    url = get_github_auth_url(state=state)
    response = RedirectResponse(url)
    response.set_cookie(key="oauth_state", value=state, max_age=300, httponly=True, samesite="lax")
    return response


@router.get("/github/callback")
async def github_callback(code: str, state: str = "", db: Session = Depends(get_db)):
    if not state or state not in _oauth_states:
        raise HTTPException(status_code=400, detail="Invalid OAuth state - possible CSRF")
    _oauth_states.discard(state)

    access_token = await exchange_code_for_token(code)
    if not access_token:
        raise HTTPException(status_code=400, detail="GitHub OAuth failed")

    github_user = await get_github_user(access_token)
    user = upsert_github_user(db, github_user)
    jwt = create_user_jwt(user)

    response = RedirectResponse(f"{settings.FRONTEND_URL}/dashboard")
    response.set_cookie(key="cs_token", value=jwt, httponly=True, samesite="lax", max_age=86400)
    return response


@router.get("/me", response_model=UserPublic)
def me(user=Depends(get_current_user)):
    return user
