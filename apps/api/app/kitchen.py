from __future__ import annotations

import asyncio
import json
import os
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import jwt
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import JWT_ALGORITHM, JWT_SECRET
from app.db import get_session
from app.models import Order, OrderStatus, Restaurant, Table
from app.orders import _order_load_options, _serialize_order
from app.realtime import get_redis, kitchen_channel, publish_kitchen_event
from app.schemas import KitchenLoginIn, KitchenLoginOut, KitchenStatusUpdate, OrderOut

router = APIRouter(prefix="/kitchen", tags=["kitchen"])

bearer_scheme = HTTPBearer(auto_error=False)

STATUS_FLOW: list[OrderStatus] = [
    OrderStatus.nouvelle,
    OrderStatus.acceptee,
    OrderStatus.en_preparation,
    OrderStatus.prete,
    OrderStatus.terminee,
]


def kitchen_pin() -> str:
    return os.getenv("KITCHEN_PIN", "nh-kitchen")


def create_kitchen_token(*, restaurant_id: UUID) -> str:
    payload: dict[str, Any] = {
        "sub": str(restaurant_id),
        "role": "kitchen",
        "exp": datetime.now(UTC) + timedelta(hours=12),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_kitchen_token(token: str) -> UUID:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from exc
    if payload.get("role") != "kitchen":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    subject = payload.get("sub")
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    try:
        return UUID(str(subject))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from exc


async def get_kitchen_restaurant_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> UUID:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return decode_kitchen_token(credentials.credentials)


def next_status(current: OrderStatus) -> OrderStatus | None:
    try:
        index = STATUS_FLOW.index(current)
    except ValueError:
        return None
    if index >= len(STATUS_FLOW) - 1:
        return None
    return STATUS_FLOW[index + 1]


@router.post("/login", response_model=KitchenLoginOut)
async def kitchen_login(
    body: KitchenLoginIn,
    session: AsyncSession = Depends(get_session),
):
    if body.pin != kitchen_pin():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    restaurant = (
        await session.execute(
            select(Restaurant).where(Restaurant.slug == body.restaurant_slug)
        )
    ).scalar_one_or_none()
    if restaurant is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    return KitchenLoginOut(
        access_token=create_kitchen_token(restaurant_id=restaurant.id),
        restaurant_id=restaurant.id,
    )


@router.get("/orders", response_model=list[OrderOut])
async def list_kitchen_orders(
    restaurant_id: UUID = Depends(get_kitchen_restaurant_id),
    session: AsyncSession = Depends(get_session),
):
    orders = (
        await session.execute(
            select(Order)
            .where(
                Order.restaurant_id == restaurant_id,
                Order.status != OrderStatus.terminee,
            )
            .options(*_order_load_options())
            .order_by(Order.number.asc())
        )
    ).scalars().all()

    result: list[OrderOut] = []
    for order in orders:
        table = await session.get(Table, order.table_id)
        label = table.label if table else "?"
        result.append(_serialize_order(order, label))
    return result


@router.patch("/orders/{order_id}", response_model=OrderOut)
async def update_kitchen_order_status(
    order_id: UUID,
    body: KitchenStatusUpdate,
    restaurant_id: UUID = Depends(get_kitchen_restaurant_id),
    session: AsyncSession = Depends(get_session),
):
    order = (
        await session.execute(
            select(Order)
            .where(Order.id == order_id, Order.restaurant_id == restaurant_id)
            .options(*_order_load_options())
        )
    ).scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    try:
        target = OrderStatus(body.status)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status",
        ) from exc

    expected = next_status(order.status)
    if expected is None or target != expected:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Invalid status transition",
        )

    order.status = target
    await session.commit()

    loaded = (
        await session.execute(
            select(Order).where(Order.id == order.id).options(*_order_load_options())
        )
    ).scalar_one()
    table = await session.get(Table, loaded.table_id)
    label = table.label if table else "?"
    out = _serialize_order(loaded, label)
    await publish_kitchen_event(
        restaurant_id,
        {
            "type": "order_updated",
            "order_id": str(loaded.id),
            "status": loaded.status.value,
        },
    )
    return out


@router.websocket("/ws")
async def kitchen_websocket(websocket: WebSocket, token: str = Query(...)):
    await websocket.accept()
    try:
        restaurant_id = decode_kitchen_token(token)
    except HTTPException:
        await websocket.close(code=4401)
        return

    client = await get_redis()
    pubsub = client.pubsub()
    channel = kitchen_channel(restaurant_id)
    await pubsub.subscribe(channel)
    try:
        while True:
            message = await pubsub.get_message(
                ignore_subscribe_messages=True, timeout=1.0
            )
            if message and message.get("type") == "message":
                data = message["data"]
                if isinstance(data, bytes):
                    data = data.decode()
                if isinstance(data, str):
                    await websocket.send_text(data)
                else:
                    await websocket.send_json(data)
            else:
                # Detect client disconnect without blocking the Redis loop forever.
                try:
                    await asyncio.wait_for(websocket.receive_text(), timeout=0.01)
                except TimeoutError:
                    continue
                except WebSocketDisconnect:
                    break
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.aclose()
