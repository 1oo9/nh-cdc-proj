"""Admin login — JWT for internal team only."""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import hash_password
from app.db import get_session
from app.main import app as fastapi_app
from app.models import AdminUser
from app.seed import DEMO_ADMIN_EMAIL


@pytest_asyncio.fixture
async def api_client(db_session: AsyncSession):
    async def override_session():
        yield db_session

    fastapi_app.dependency_overrides[get_session] = override_session
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    fastapi_app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_admin_login_returns_access_token(api_client, db_session):
    db_session.add(
        AdminUser(email=DEMO_ADMIN_EMAIL, password_hash=hash_password("nh-admin"))
    )
    await db_session.commit()

    response = await api_client.post(
        "/admin/login",
        json={"email": DEMO_ADMIN_EMAIL, "password": "nh-admin"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_admin_login_rejected_with_wrong_password(api_client, db_session):
    db_session.add(
        AdminUser(email=DEMO_ADMIN_EMAIL, password_hash=hash_password("nh-admin"))
    )
    await db_session.commit()

    response = await api_client.post(
        "/admin/login",
        json={"email": DEMO_ADMIN_EMAIL, "password": "wrong"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_restaurants_require_auth(api_client):
    response = await api_client.get("/admin/restaurants")
    assert response.status_code == 401
