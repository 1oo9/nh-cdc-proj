from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_session
from app.models import (
    Option,
    OptionGroup,
    Order,
    OrderItem,
    OrderItemOption,
    OrderStatus,
    Product,
    Table,
)
from app.schemas import OrderCreate, OrderItemOut, OrderOut
from app.realtime import publish_kitchen_event

router = APIRouter(tags=["orders"])


def _order_load_options():
    return (
        selectinload(Order.items)
        .selectinload(OrderItem.options)
        .selectinload(OrderItemOption.option),
        selectinload(Order.items).selectinload(OrderItem.product),
    )


def _serialize_order(order: Order, table_label: str) -> OrderOut:
    items_out: list[OrderItemOut] = []
    for item in order.items:
        product_name = item.product.name if item.product is not None else str(item.product_id)
        option_names = [
            link.option.name for link in item.options if link.option is not None
        ]
        items_out.append(
            OrderItemOut(
                product_name=product_name,
                quantity=item.quantity,
                unit_price_cents=item.unit_price_cents,
                options=option_names,
            )
        )
    return OrderOut(
        id=order.id,
        number=order.number,
        status=order.status.value,
        table_label=table_label,
        total_cents=order.total_cents,
        items=items_out,
    )


@router.post("/orders")
async def create_order(
    body: OrderCreate,
    session: AsyncSession = Depends(get_session),
):
    table = (
        await session.execute(
            select(Table).where(
                Table.public_token == body.table_token,
                Table.active.is_(True),
            )
        )
    ).scalar_one_or_none()
    if table is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Table not found")

    existing = (
        await session.execute(
            select(Order)
            .where(
                Order.restaurant_id == table.restaurant_id,
                Order.idempotency_key == body.idempotency_key,
            )
            .options(*_order_load_options())
        )
    ).scalar_one_or_none()
    if existing is not None:
        return JSONResponse(
            status_code=200,
            content=_serialize_order(existing, table.label).model_dump(mode="json"),
        )

    built_items: list[tuple[Product, int, list[Option], int]] = []
    total = 0
    for line in body.items:
        product = await session.get(Product, line.product_id)
        if (
            product is None
            or product.restaurant_id != table.restaurant_id
            or not product.available
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Product unavailable",
            )
        options: list[Option] = []
        unit = product.price_cents
        for option_id in line.option_ids:
            option = await session.get(Option, option_id)
            if option is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid option",
                )
            group = await session.get(OptionGroup, option.option_group_id)
            if group is None or group.product_id != product.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid option",
                )
            options.append(option)
            unit += option.price_delta_cents
        built_items.append((product, line.quantity, options, unit))
        total += unit * line.quantity

    next_number = (
        await session.execute(
            select(func.coalesce(func.max(Order.number), 0)).where(
                Order.restaurant_id == table.restaurant_id
            )
        )
    ).scalar_one()
    order = Order(
        restaurant_id=table.restaurant_id,
        table_id=table.id,
        number=int(next_number) + 1,
        status=OrderStatus.nouvelle,
        total_cents=total,
        idempotency_key=body.idempotency_key,
    )
    session.add(order)
    await session.flush()

    for product, quantity, options, unit in built_items:
        item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=quantity,
            unit_price_cents=unit,
        )
        session.add(item)
        await session.flush()
        for option in options:
            session.add(
                OrderItemOption(
                    order_item_id=item.id,
                    option_id=option.id,
                    price_delta_cents=option.price_delta_cents,
                )
            )

    await session.commit()

    loaded = (
        await session.execute(
            select(Order).where(Order.id == order.id).options(*_order_load_options())
        )
    ).scalar_one()
    out = _serialize_order(loaded, table.label)
    await publish_kitchen_event(
        table.restaurant_id,
        {"type": "order_created", "order_id": str(loaded.id)},
    )
    return JSONResponse(
        status_code=201,
        content=out.model_dump(mode="json"),
    )


@router.get("/orders/{order_id}", response_model=OrderOut)
async def get_order(
    order_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    order = (
        await session.execute(
            select(Order).where(Order.id == order_id).options(*_order_load_options())
        )
    ).scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    table = await session.get(Table, order.table_id)
    label = table.label if table else "?"
    return _serialize_order(order, label)
