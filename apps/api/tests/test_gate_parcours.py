"""S10 gate — full parcours API smoke (QR menu → order → cuisine → terminée)."""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.main import app as fastapi_app
from app.models import (
    Category,
    Option,
    OptionGroup,
    Product,
    Restaurant,
    Table,
)


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
async def gate_context(db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("KITCHEN_PIN", "nh-kitchen")
    restaurant = Restaurant(name="Chicken Street Paris", slug="chicken-street-paris")
    db_session.add(restaurant)
    await db_session.flush()
    category = Category(
        restaurant_id=restaurant.id, name="Burgers", sort_order=1, active=True
    )
    db_session.add(category)
    await db_session.flush()
    product = Product(
        restaurant_id=restaurant.id,
        category_id=category.id,
        name="Chicken Burger",
        price_cents=1250,
        available=True,
        sort_order=1,
    )
    db_session.add(product)
    await db_session.flush()
    group = OptionGroup(
        product_id=product.id,
        name="Suppléments",
        required=False,
        min_select=0,
        max_select=3,
    )
    db_session.add(group)
    await db_session.flush()
    option = Option(option_group_id=group.id, name="fromage", price_delta_cents=100)
    db_session.add(option)
    token = uuid.uuid4().hex
    table = Table(
        restaurant_id=restaurant.id,
        label="14",
        public_token=token,
        active=True,
    )
    db_session.add(table)
    await db_session.commit()
    return {
        "token": token,
        "product_id": str(product.id),
        "option_id": str(option.id),
        "slug": restaurant.slug,
        "pin": "nh-kitchen",
    }


@pytest.mark.asyncio
async def test_gate_full_parcours_menu_order_kitchen_to_terminee(
    api_client, gate_context
):
    menu = await api_client.get(f"/t/{gate_context['token']}/menu")
    assert menu.status_code == 200
    body = menu.json()
    assert body["restaurant"]["name"] == "Chicken Street Paris"
    assert body["table"]["label"] == "14"
    assert any(
        p["name"] == "Chicken Burger"
        for c in body["categories"]
        for p in c["products"]
    )

    created = await api_client.post(
        "/orders",
        json={
            "table_token": gate_context["token"],
            "idempotency_key": str(uuid.uuid4()),
            "items": [
                {
                    "product_id": gate_context["product_id"],
                    "quantity": 1,
                    "option_ids": [gate_context["option_id"]],
                }
            ],
        },
    )
    assert created.status_code == 201
    order = created.json()
    assert order["status"] == "nouvelle"
    assert order["table_label"] == "14"
    assert order["total_cents"] == 1350
    order_id = order["id"]

    confirmation = await api_client.get(f"/orders/{order_id}")
    assert confirmation.status_code == 200
    assert confirmation.json()["number"] == order["number"]

    login = await api_client.post(
        "/kitchen/login",
        json={
            "restaurant_slug": gate_context["slug"],
            "pin": gate_context["pin"],
        },
    )
    assert login.status_code == 200
    kitchen_token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {kitchen_token}"}

    listed = await api_client.get("/kitchen/orders", headers=headers)
    assert listed.status_code == 200
    assert any(t["id"] == order_id for t in listed.json())

    for status in ("acceptee", "en_preparation", "prete", "terminee"):
        patched = await api_client.patch(
            f"/kitchen/orders/{order_id}",
            headers=headers,
            json={"status": status},
        )
        assert patched.status_code == 200, patched.text
        assert patched.json()["status"] == status

    final_list = await api_client.get("/kitchen/orders", headers=headers)
    assert final_list.status_code == 200
    assert all(t["id"] != order_id for t in final_list.json())
