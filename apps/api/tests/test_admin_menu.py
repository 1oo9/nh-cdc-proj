"""Admin menu CRUD — categories, products, options, availability, sort order."""

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
async def test_admin_creates_and_lists_category(api_client, auth_headers, restaurant):
    create = await api_client.post(
        f"/admin/restaurants/{restaurant.id}/categories",
        headers=auth_headers,
        json={"name": "Burgers", "sort_order": 1, "active": True},
    )
    assert create.status_code == 201
    body = create.json()
    assert body["name"] == "Burgers"
    assert body["restaurant_id"] == str(restaurant.id)

    listed = await api_client.get(
        f"/admin/restaurants/{restaurant.id}/categories",
        headers=auth_headers,
    )
    assert listed.status_code == 200
    names = [c["name"] for c in listed.json()]
    assert "Burgers" in names


@pytest.mark.asyncio
async def test_admin_creates_product_with_price_cents_and_availability(
    api_client, auth_headers, restaurant
):
    cat = await api_client.post(
        f"/admin/restaurants/{restaurant.id}/categories",
        headers=auth_headers,
        json={"name": "Burgers", "sort_order": 1, "active": True},
    )
    category_id = cat.json()["id"]

    create = await api_client.post(
        f"/admin/restaurants/{restaurant.id}/products",
        headers=auth_headers,
        json={
            "category_id": category_id,
            "name": "Chicken Burger",
            "description": "Classic",
            "price_cents": 1250,
            "photo_url": "https://example.com/burger.jpg",
            "available": True,
            "sort_order": 1,
        },
    )
    assert create.status_code == 201
    product = create.json()
    assert product["price_cents"] == 1250
    assert product["available"] is True
    assert product["photo_url"] == "https://example.com/burger.jpg"

    patch = await api_client.patch(
        f"/admin/products/{product['id']}",
        headers=auth_headers,
        json={"available": False, "sort_order": 2},
    )
    assert patch.status_code == 200
    assert patch.json()["available"] is False
    assert patch.json()["sort_order"] == 2


@pytest.mark.asyncio
async def test_admin_creates_option_group_and_option(api_client, auth_headers, restaurant):
    cat = await api_client.post(
        f"/admin/restaurants/{restaurant.id}/categories",
        headers=auth_headers,
        json={"name": "Burgers", "sort_order": 1, "active": True},
    )
    product = await api_client.post(
        f"/admin/restaurants/{restaurant.id}/products",
        headers=auth_headers,
        json={
            "category_id": cat.json()["id"],
            "name": "Chicken Burger",
            "price_cents": 1250,
            "available": True,
            "sort_order": 1,
        },
    )
    product_id = product.json()["id"]

    group = await api_client.post(
        f"/admin/products/{product_id}/option-groups",
        headers=auth_headers,
        json={
            "name": "Suppléments",
            "required": False,
            "min_select": 0,
            "max_select": 3,
        },
    )
    assert group.status_code == 201
    group_id = group.json()["id"]

    option = await api_client.post(
        f"/admin/option-groups/{group_id}/options",
        headers=auth_headers,
        json={"name": "fromage", "price_delta_cents": 100},
    )
    assert option.status_code == 201
    assert option.json()["price_delta_cents"] == 100


@pytest.mark.asyncio
async def test_admin_updates_restaurant_name(api_client, auth_headers, restaurant):
    response = await api_client.patch(
        f"/admin/restaurants/{restaurant.id}",
        headers=auth_headers,
        json={"name": "Chicken Street Paris Centre"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Chicken Street Paris Centre"
