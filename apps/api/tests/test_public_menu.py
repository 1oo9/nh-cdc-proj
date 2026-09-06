"""Public menu by opaque table token — no auth."""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.main import app as fastapi_app
from app.models import Category, Option, OptionGroup, Product, Restaurant, Table


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
async def seeded_table(db_session: AsyncSession):
    restaurant = Restaurant(name="Chicken Street Paris", slug="chicken-street-paris")
    db_session.add(restaurant)
    await db_session.flush()

    category = Category(
        restaurant_id=restaurant.id, name="Burgers", sort_order=1, active=True
    )
    db_session.add(category)
    await db_session.flush()

    available = Product(
        restaurant_id=restaurant.id,
        category_id=category.id,
        name="Chicken Burger",
        description="Classic",
        price_cents=1250,
        photo_url="https://example.com/burger.jpg",
        available=True,
        sort_order=1,
    )
    unavailable = Product(
        restaurant_id=restaurant.id,
        category_id=category.id,
        name="Sold Out Wrap",
        price_cents=900,
        available=False,
        sort_order=2,
    )
    db_session.add_all([available, unavailable])
    await db_session.flush()

    group = OptionGroup(
        product_id=available.id,
        name="Suppléments",
        required=False,
        min_select=0,
        max_select=3,
    )
    db_session.add(group)
    await db_session.flush()
    db_session.add(
        Option(option_group_id=group.id, name="fromage", price_delta_cents=100)
    )

    token = uuid.uuid4().hex
    table = Table(
        restaurant_id=restaurant.id,
        label="14",
        public_token=token,
        active=True,
    )
    db_session.add(table)
    await db_session.commit()
    return {"token": token, "restaurant_id": restaurant.id, "label": "14"}


@pytest.mark.asyncio
async def test_public_menu_resolved_by_opaque_token(api_client, seeded_table):
    response = await api_client.get(f"/t/{seeded_table['token']}/menu")
    assert response.status_code == 200
    body = response.json()
    assert body["restaurant"]["name"] == "Chicken Street Paris"
    assert body["table"]["label"] == "14"
    assert body["table"]["public_token"] == seeded_table["token"]
    names = [p["name"] for c in body["categories"] for p in c["products"]]
    assert "Chicken Burger" in names
    assert "Sold Out Wrap" not in names
    burger = next(
        p for c in body["categories"] for p in c["products"] if p["name"] == "Chicken Burger"
    )
    assert burger["price_cents"] == 1250
    assert burger["photo_url"] == "https://example.com/burger.jpg"
    assert burger["options"][0]["name"] == "fromage"
    assert burger["options"][0]["price_delta_cents"] == 100


@pytest.mark.asyncio
async def test_public_menu_unknown_token_returns_404(api_client):
    response = await api_client.get(f"/t/{uuid.uuid4().hex}/menu")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_public_menu_inactive_table_returns_404(api_client, db_session):
    restaurant = Restaurant(name="X", slug="x")
    db_session.add(restaurant)
    await db_session.flush()
    token = uuid.uuid4().hex
    db_session.add(
        Table(
            restaurant_id=restaurant.id,
            label="99",
            public_token=token,
            active=False,
        )
    )
    await db_session.commit()

    response = await api_client.get(f"/t/{token}/menu")
    assert response.status_code == 404
