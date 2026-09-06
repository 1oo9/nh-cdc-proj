"""Admin tables + QR generation."""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import create_access_token, hash_password
from app.db import get_session
from app.main import app as fastapi_app
from app.models import AdminUser, Restaurant
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


@pytest_asyncio.fixture
async def auth_headers(db_session: AsyncSession):
    admin = AdminUser(email=DEMO_ADMIN_EMAIL, password_hash=hash_password("nh-admin"))
    db_session.add(admin)
    await db_session.commit()
    token = create_access_token(subject=str(admin.id))
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def restaurant(db_session: AsyncSession):
    resto = Restaurant(name="Chicken Street Paris", slug="chicken-street-paris")
    db_session.add(resto)
    await db_session.commit()
    await db_session.refresh(resto)
    return resto


@pytest.mark.asyncio
async def test_admin_creates_table_with_opaque_token(api_client, auth_headers, restaurant):
    response = await api_client.post(
        f"/admin/restaurants/{restaurant.id}/tables",
        headers=auth_headers,
        json={"label": "14"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["label"] == "14"
    assert body["public_token"]
    assert body["public_token"] != "14"
    assert len(body["public_token"]) >= 16


@pytest.mark.asyncio
async def test_admin_lists_tables(api_client, auth_headers, restaurant):
    await api_client.post(
        f"/admin/restaurants/{restaurant.id}/tables",
        headers=auth_headers,
        json={"label": "12"},
    )
    listed = await api_client.get(
        f"/admin/restaurants/{restaurant.id}/tables",
        headers=auth_headers,
    )
    assert listed.status_code == 200
    labels = [t["label"] for t in listed.json()]
    assert "12" in labels


@pytest.mark.asyncio
async def test_admin_downloads_qr_png_for_table(api_client, auth_headers, restaurant):
    created = await api_client.post(
        f"/admin/restaurants/{restaurant.id}/tables",
        headers=auth_headers,
        json={"label": "14"},
    )
    table_id = created.json()["id"]
    response = await api_client.get(
        f"/admin/tables/{table_id}/qr.png",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content[:8] == b"\x89PNG\r\n\x1a\n"
