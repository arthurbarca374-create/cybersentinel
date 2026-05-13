from datetime import datetime
from typing import Optional
import httpx
from sqlalchemy.orm import Session
from backend.core.config import get_settings
from backend.core.security import create_access_token
from backend.models.user import User

settings = get_settings()

GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"


def get_github_auth_url(state: str = "") -> str:
    params = (
        f"client_id={settings.GITHUB_CLIENT_ID}"
        f"&redirect_uri={settings.GITHUB_REDIRECT_URI}"
        f"&scope=read:user,user:email"
        f"&state={state}"
    )
    return f"{GITHUB_AUTH_URL}?{params}"


async def exchange_code_for_token(code: str) -> Optional[str]:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            GITHUB_TOKEN_URL,
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.GITHUB_REDIRECT_URI,
            },
        )
        data = resp.json()
        return data.get("access_token")


async def get_github_user(access_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            GITHUB_USER_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        return resp.json()


def upsert_github_user(db: Session, github_user: dict) -> User:
    github_id = str(github_user["id"])
    user = db.query(User).filter(User.github_id == github_id).first()

    if user is None:
        user = User(
            github_id=github_id,
            username=github_user.get("login", f"user_{github_id}"),
            email=github_user.get("email"),
            avatar_url=github_user.get("avatar_url"),
            bio=github_user.get("bio"),
            is_verified=True,
            trial_started_at=datetime.utcnow(),
        )
        db.add(user)
    else:
        user.avatar_url = github_user.get("avatar_url", user.avatar_url)
        user.email = github_user.get("email") or user.email

    user.last_login = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user


def create_user_jwt(user: User) -> str:
    return create_access_token({"sub": str(user.id), "username": user.username})
