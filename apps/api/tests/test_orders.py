"""Order submit — token only, price snapshot, availability, idempotency."""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.main import app as fastapi_app
from app.models import (
    Category,
    Option,
    OptionGroup,
    Order,
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
async def menu_context(db_session: AsyncSession):
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
        "restaurant_id": restaurant.id,
    }


@pytest.mark.asyncio
async def test_order_created_from_table_token_with_price_snapshot(
    api_client, menu_context, db_session
):
    response = await api_client.post(
        "/orders",
        json={
            "table_token": menu_context["token"],
            "idempotency_key": str(uuid.uuid4()),
            "items": [
                {
                    "product_id": menu_context["product_id"],
                    "quantity": 2,
                    "option_ids": [menu_context["option_id"]],
                }
            ],
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "nouvelle"
    assert body["table_label"] == "14"
    assert body["number"] == 1
    # 2 × (1250 + 100) = 2700
    assert body["total_cents"] == 2700
    assert "email" not in body
    assert "phone" not in body

    order = (await db_session.execute(select(Order))).scalar_one()
    assert order.status == OrderStatus.nouvelle
    assert order.total_cents == 2700


@pytest.mark.asyncio
async def test_order_idempotent_with_same_key(api_client, menu_context):
    key = str(uuid.uuid4())
    payload = {
        "table_token": menu_context["token"],
        "idempotency_key": key,
        "items": [
            {
                "product_id": menu_context["product_id"],
                "quantity": 1,
                "option_ids": [],
            }
        ],
    }
    first = await api_client.post("/orders", json=payload)
    second = await api_client.post("/orders", json=payload)
    assert first.status_code == 201
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert first.json()["number"] == second.json()["number"]


@pytest.mark.asyncio
async def test_order_rejected_when_product_unavailable(
    api_client, menu_context, db_session
):
    product = await db_session.get(Product, uuid.UUID(menu_context["product_id"]))
    assert product is not None
    product.available = False
    await db_session.commit()

    response = await api_client.post(
        "/orders",
        json={
            "table_token": menu_context["token"],
            "idempotency_key": str(uuid.uuid4()),
            "items": [
                {
                    "product_id": menu_context["product_id"],
                    "quantity": 1,
                    "option_ids": [],
                }
            ],
        },
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_order_rejected_for_unknown_table_token(api_client, menu_context):
    response = await api_client.post(
        "/orders",
        json={
            "table_token": uuid.uuid4().hex,
            "idempotency_key": str(uuid.uuid4()),
            "items": [
                {
                    "product_id": menu_context["product_id"],
                    "quantity": 1,
                    "option_ids": [],
                }
            ],
        },
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_order_number_increments_per_restaurant(api_client, menu_context):
    for expected in (1, 2):
        response = await api_client.post(
            "/orders",
            json={
                "table_token": menu_context["token"],
                "idempotency_key": str(uuid.uuid4()),
                "items": [
                    {
                        "product_id": menu_context["product_id"],
                        "quantity": 1,
                        "option_ids": [],
                    }
                ],
            },
        )
        assert response.status_code == 201
        assert response.json()["number"] == expected


@pytest.mark.asyncio
async def test_get_order_returns_confirmation_payload(api_client, menu_context):
    created = await api_client.post(
        "/orders",
        json={
            "table_token": menu_context["token"],
            "idempotency_key": str(uuid.uuid4()),
            "items": [
                {
                    "product_id": menu_context["product_id"],
                    "quantity": 1,
                    "option_ids": [menu_context["option_id"]],
                }
            ],
        },
    )
    assert created.status_code == 201
    order_id = created.json()["id"]

    response = await api_client.get(f"/orders/{order_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == order_id
    assert body["table_label"] == "14"
    assert body["items"][0]["product_name"] == "Chicken Burger"
    assert "fromage" in body["items"][0]["options"]
