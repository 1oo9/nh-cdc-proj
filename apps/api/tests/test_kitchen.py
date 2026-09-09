"""Kitchen board — PIN auth, list open tickets, advance status."""

from __future__ import annotations

import os
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.main import app as fastapi_app
from app.models import (
    Category,
    Order,
    OrderItem,
    OrderStatus,
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
async def kitchen_context(db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("KITCHEN_PIN", "4242")
    # Re-read env in kitchen module if already imported — tests set before requests.
    restaurant = Restaurant(name="Chicken Street Paris", slug="chicken-street-paris")
    db_session.add(restaurant)
    await db_session.flush()
    table = Table(
        restaurant_id=restaurant.id,
        label="14",
        public_token=uuid.uuid4().hex,
        active=True,
    )
    category = Category(
        restaurant_id=restaurant.id, name="Burgers", sort_order=1, active=True
    )
    db_session.add_all([table, category])
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
    order = Order(
        restaurant_id=restaurant.id,
        table_id=table.id,
        number=1,
        status=OrderStatus.nouvelle,
        total_cents=1250,
        idempotency_key=uuid.uuid4().hex,
    )
    db_session.add(order)
    await db_session.flush()
    db_session.add(
        OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=1,
            unit_price_cents=1250,
        )
    )
    await db_session.commit()
    return {
        "restaurant_id": restaurant.id,
        "slug": restaurant.slug,
        "order_id": order.id,
        "pin": "4242",
    }


async def _login(client: AsyncClient, slug: str, pin: str) -> str:
    response = await client.post(
        "/kitchen/login",
        json={"restaurant_slug": slug, "pin": pin},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_kitchen_login_returns_token(api_client, kitchen_context, monkeypatch):
    monkeypatch.setenv("KITCHEN_PIN", "4242")
    response = await api_client.post(
        "/kitchen/login",
        json={
            "restaurant_slug": kitchen_context["slug"],
            "pin": kitchen_context["pin"],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert "access_token" in body
    assert body["restaurant_id"] == str(kitchen_context["restaurant_id"])


@pytest.mark.asyncio
async def test_kitchen_login_rejected_with_wrong_pin(
    api_client, kitchen_context, monkeypatch
):
    monkeypatch.setenv("KITCHEN_PIN", "4242")
    response = await api_client.post(
        "/kitchen/login",
        json={"restaurant_slug": kitchen_context["slug"], "pin": "0000"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_kitchen_orders_require_auth(api_client):
    response = await api_client.get("/kitchen/orders")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_kitchen_lists_open_orders_with_table_and_lines(
    api_client, kitchen_context, monkeypatch
):
    monkeypatch.setenv("KITCHEN_PIN", "4242")
    token = await _login(api_client, kitchen_context["slug"], kitchen_context["pin"])
    response = await api_client.get(
        "/kitchen/orders",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    ticket = body[0]
    assert ticket["number"] == 1
    assert ticket["table_label"] == "14"
    assert ticket["status"] == "nouvelle"
    assert ticket["total_cents"] == 1250
    assert ticket["items"][0]["product_name"] == "Chicken Burger"


@pytest.mark.asyncio
async def test_kitchen_hides_terminee_orders(
    api_client, kitchen_context, db_session, monkeypatch
):
    monkeypatch.setenv("KITCHEN_PIN", "4242")
    order = await db_session.get(Order, kitchen_context["order_id"])
    assert order is not None
    order.status = OrderStatus.terminee
    await db_session.commit()

    token = await _login(api_client, kitchen_context["slug"], kitchen_context["pin"])
    response = await api_client.get(
        "/kitchen/orders",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_kitchen_advances_status_nouvelle_to_acceptee(
    api_client, kitchen_context, monkeypatch
):
    monkeypatch.setenv("KITCHEN_PIN", "4242")
    token = await _login(api_client, kitchen_context["slug"], kitchen_context["pin"])
    response = await api_client.patch(
        f"/kitchen/orders/{kitchen_context['order_id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "acceptee"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "acceptee"


@pytest.mark.asyncio
async def test_kitchen_rejects_invalid_status_skip(
    api_client, kitchen_context, monkeypatch
):
    monkeypatch.setenv("KITCHEN_PIN", "4242")
    token = await _login(api_client, kitchen_context["slug"], kitchen_context["pin"])
    response = await api_client.patch(
        f"/kitchen/orders/{kitchen_context['order_id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "prete"},
    )
    assert response.status_code == 409
