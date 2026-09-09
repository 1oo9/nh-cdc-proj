"""Kitchen realtime — publish on order create, WebSocket fan-out."""

from __future__ import annotations

import json
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.testclient import TestClient

from app.db import get_session
from app.kitchen import create_kitchen_token
from app.main import app as fastapi_app
from app.models import Category, Product, Restaurant, Table
from app.realtime import kitchen_channel


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
async def order_ready(db_session: AsyncSession):
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
    await db_session.commit()
    return {
        "restaurant_id": restaurant.id,
        "token": table.public_token,
        "product_id": str(product.id),
    }


def test_kitchen_channel_scoped_to_restaurant():
    rid = uuid.uuid4()
    assert kitchen_channel(rid) == f"kitchen:{rid}"


@pytest.mark.asyncio
async def test_order_create_publishes_kitchen_event(
    api_client, order_ready, monkeypatch
):
    published: list[tuple] = []

    async def fake_publish(restaurant_id, payload):
        published.append((restaurant_id, payload))

    monkeypatch.setattr("app.orders.publish_kitchen_event", fake_publish)

    response = await api_client.post(
        "/orders",
        json={
            "table_token": order_ready["token"],
            "idempotency_key": str(uuid.uuid4()),
            "items": [
                {
                    "product_id": order_ready["product_id"],
                    "quantity": 1,
                    "option_ids": [],
                }
            ],
        },
    )
    assert response.status_code == 201
    assert len(published) == 1
    restaurant_id, payload = published[0]
    assert restaurant_id == order_ready["restaurant_id"]
    assert payload["type"] == "order_created"
    assert payload["order_id"] == response.json()["id"]


@pytest.mark.asyncio
async def test_kitchen_status_update_publishes_event(
    api_client, order_ready, monkeypatch
):
    monkeypatch.setenv("KITCHEN_PIN", "4242")
    published: list[tuple] = []

    async def fake_publish(restaurant_id, payload):
        published.append((restaurant_id, payload))

    monkeypatch.setattr("app.orders.publish_kitchen_event", fake_publish)
    monkeypatch.setattr("app.kitchen.publish_kitchen_event", fake_publish)

    created = await api_client.post(
        "/orders",
        json={
            "table_token": order_ready["token"],
            "idempotency_key": str(uuid.uuid4()),
            "items": [
                {
                    "product_id": order_ready["product_id"],
                    "quantity": 1,
                    "option_ids": [],
                }
            ],
        },
    )
    assert created.status_code == 201
    published.clear()

    login = await api_client.post(
        "/kitchen/login",
        json={"restaurant_slug": "chicken-street-paris", "pin": "4242"},
    )
    assert login.status_code == 200
    kitchen_token = login.json()["access_token"]
    order_id = created.json()["id"]

    patched = await api_client.patch(
        f"/kitchen/orders/{order_id}",
        headers={"Authorization": f"Bearer {kitchen_token}"},
        json={"status": "acceptee"},
    )
    assert patched.status_code == 200
    assert len(published) == 1
    assert published[0][1]["type"] == "order_updated"
    assert published[0][1]["status"] == "acceptee"


@pytest.mark.asyncio
async def test_kitchen_websocket_forwards_redis_message(db_session, monkeypatch):
    restaurant = Restaurant(name="WS Resto", slug=f"ws-{uuid.uuid4().hex[:8]}")
    db_session.add(restaurant)
    await db_session.commit()
    token = create_kitchen_token(restaurant_id=restaurant.id)

    class FakePubSub:
        def __init__(self):
            self._sent = False

        async def subscribe(self, *channels):
            return None

        async def unsubscribe(self, *channels):
            return None

        async def aclose(self):
            return None

        async def get_message(self, ignore_subscribe_messages=True, timeout=1.0):
            if not self._sent:
                self._sent = True
                return {
                    "type": "message",
                    "data": json.dumps({"type": "order_created", "order_id": "abc"}),
                }
            return None

    class FakeRedis:
        def pubsub(self):
            return FakePubSub()

    async def fake_get_redis():
        return FakeRedis()

    monkeypatch.setattr("app.kitchen.get_redis", fake_get_redis)

    client = TestClient(fastapi_app)
    with client.websocket_connect(f"/kitchen/ws?token={token}") as ws:
        data = ws.receive_json()
        assert data["type"] == "order_created"
        assert data["order_id"] == "abc"
