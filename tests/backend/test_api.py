import pytest
import os

os.environ["SECRET_KEY"] = "test-secret-key-for-ci"
os.environ["GITHUB_CLIENT_ID"] = "dummy"
os.environ["GITHUB_CLIENT_SECRET"] = "dummy"
os.environ["FRONTEND_URL"] = "http://testserver"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from backend.db.database import Base, get_db

TEST_DATABASE_URL = "sqlite://"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_register_and_login():
    res = client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123",
    })
    assert res.status_code == 201, res.text
    data = res.json()
    assert "access_token" in data
    assert data["user"]["username"] == "testuser"
    assert data["user"]["is_trial_active"] is True
    assert data["user"]["trial_scans_remaining"] == 10

    res = client.post("/api/auth/login", json={
        "username": "testuser",
        "password": "password123",
    })
    assert res.status_code == 200
    token = res.json()["access_token"]

    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["username"] == "testuser"


def test_trial_status():
    client.post("/api/auth/register", json={
        "username": "trialuser",
        "email": "trial@example.com",
        "password": "password123",
    })
    login = client.post("/api/auth/login", json={
        "username": "trialuser",
        "password": "password123",
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/users/trial/status", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["is_active"] is True
    assert data["scans_remaining"] == 10

    res = client.post("/api/users/trial/use-scan", headers=headers)
    assert res.status_code == 200
    assert res.json()["scans_remaining"] == 9


def test_community_members():
    res = client.get("/api/users/community/members")
    assert res.status_code == 200
    assert "total_members" in res.json()


def test_unauthenticated_me():
    res = client.get("/api/auth/me")
    assert res.status_code == 401


# ── New Feature Tests ─────────────────────────────────────

def test_scan_types():
    res = client.get("/api/scans/types")
    assert res.status_code == 200
    assert "scan_types" in res.json()


def test_targets_crud():
    token = _register_and_login("targetuser")

    res = client.post("/api/scans/targets", json={
        "name": "Test Server",
        "host": "192.168.1.1",
        "port": 80,
        "notes": "Test target",
    }, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 201
    target_id = res.json()["id"]

    res = client.get("/api/scans/targets", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert len(res.json()) >= 1

    res = client.delete(f"/api/scans/targets/{target_id}", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200


def test_scan_run():
    token = _register_and_login("scanuser")
    target_id = _create_target(token, "scanhost.local")

    res = client.post("/api/scans/run", json={
        "target_id": target_id,
        "scan_type": "quick",
    }, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 201
    assert res.json()["status"] == "pending"
    assert res.json()["scan_type"] == "quick"


def test_org_creation():
    token = _register_and_login("orguser")

    res = client.post("/api/orgs", json={
        "name": "Test Org",
        "slug": "test-org",
        "description": "A test organization",
    }, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Test Org"
    assert data["slug"] == "test-org"

    res = client.get("/api/orgs", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert len(res.json()) >= 1


def test_threat_lookup():
    token = _register_and_login("threatuser")
    res = client.post("/api/threat/lookup", json={
        "indicator": "8.8.8.8",
        "indicator_type": "ip",
    }, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["indicator"] == "8.8.8.8"
    assert "sources" in data
    assert "reputation" in data


def test_blockchain_analysis():
    token = _register_and_login("blockuser")
    res = client.post("/api/blockchain/analyze", json={
        "chain": "bitcoin",
        "address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
    }, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["chain"] == "bitcoin"
    assert data["valid_format"] is True


def test_ai_analysis_requires_completed_scan():
    token = _register_and_login("aiuser")
    res = client.post("/api/ai/analyze", json={
        "scan_id": 999,
        "model": "default",
    }, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 404


def test_ai_models():
    res = client.get("/api/ai/models")
    assert res.status_code == 200
    assert "models" in res.json()


# ── Helpers ──────────────────────────────────────────────

def _register_and_login(username: str) -> str:
    client.post("/api/auth/register", json={
        "username": username,
        "email": f"{username}@test.com",
        "password": "password123",
    })
    res = client.post("/api/auth/login", json={
        "username": username,
        "password": "password123",
    })
    return res.json()["access_token"]


def _create_target(token: str, host: str) -> int:
    res = client.post("/api/scans/targets", json={
        "name": f"Target {host}",
        "host": host,
    }, headers={"Authorization": f"Bearer {token}"})
    return res.json()["id"]
