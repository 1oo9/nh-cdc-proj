"""Schema behaviours locked for S1 — tenant, cents, opaque table token, no diner PII."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models import (
    Category,
    Option,
    OptionGroup,
    Order,
    OrderItem,
    OrderItemOption,
    OrderStatus,
    Payment,
    Product,
    Restaurant,
    Table,
)


@pytest.mark.asyncio
async def test_table_resolved_by_opaque_public_token(db_session):
    restaurant = Restaurant(name="Chicken Street Paris", slug="chicken-street-paris")
    db_session.add(restaurant)
    await db_session.flush()

    token = uuid.uuid4().hex
    table = Table(restaurant_id=restaurant.id, label="14", public_token=token)
    db_session.add(table)
    await db_session.commit()

    found = (
        await db_session.execute(select(Table).where(Table.public_token == token))
    ).scalar_one()
    assert found.label == "14"
    assert found.restaurant_id == restaurant.id
    assert found.public_token != "14"


@pytest.mark.asyncio
async def test_product_price_stored_as_integer_cents(db_session):
    restaurant = Restaurant(name="Chicken Street Paris", slug="chicken-street-paris")
    db_session.add(restaurant)
    await db_session.flush()
    category = Category(restaurant_id=restaurant.id, name="Burgers", sort_order=1)
    db_session.add(category)
    await db_session.flush()

    product = Product(
        restaurant_id=restaurant.id,
        category_id=category.id,
        name="Chicken Burger",
        description="Classic",
        price_cents=1250,
        available=True,
        sort_order=1,
    )
    db_session.add(product)
    await db_session.commit()

    loaded = (
        await db_session.execute(select(Product).where(Product.name == "Chicken Burger"))
    ).scalar_one()
    assert loaded.price_cents == 1250
    assert isinstance(loaded.price_cents, int)


@pytest.mark.asyncio
async def test_category_and_product_carry_restaurant_id(db_session):
    restaurant = Restaurant(name="Chicken Street Paris", slug="chicken-street-paris")
    db_session.add(restaurant)
    await db_session.flush()
    category = Category(restaurant_id=restaurant.id, name="Boissons", sort_order=2)
    db_session.add(category)
    await db_session.flush()
    product = Product(
        restaurant_id=restaurant.id,
        category_id=category.id,
        name="Coca-Cola",
        price_cents=300,
        available=True,
        sort_order=1,
    )
    db_session.add(product)
    await db_session.commit()

    assert category.restaurant_id == restaurant.id
    assert product.restaurant_id == restaurant.id


@pytest.mark.asyncio
async def test_order_has_no_diner_pii_columns():
    forbidden = {"name", "email", "phone", "device_id", "customer_name", "customer_email"}
    columns = set(Order.__table__.columns.keys())
    assert forbidden.isdisjoint(columns)


@pytest.mark.asyncio
async def test_order_number_unique_per_restaurant_not_globally(db_session):
    a = Restaurant(name="A", slug="resto-a")
    b = Restaurant(name="B", slug="resto-b")
    db_session.add_all([a, b])
    await db_session.flush()

    table_a = Table(restaurant_id=a.id, label="1", public_token=uuid.uuid4().hex)
    table_b = Table(restaurant_id=b.id, label="1", public_token=uuid.uuid4().hex)
    db_session.add_all([table_a, table_b])
    await db_session.flush()

    db_session.add(
        Order(
            restaurant_id=a.id,
            table_id=table_a.id,
            number=152,
            status=OrderStatus.nouvelle,
            total_cents=1000,
        )
    )
    db_session.add(
        Order(
            restaurant_id=b.id,
            table_id=table_b.id,
            number=152,
            status=OrderStatus.nouvelle,
            total_cents=2000,
        )
    )
    await db_session.commit()

    db_session.add(
        Order(
            restaurant_id=a.id,
            table_id=table_a.id,
            number=152,
            status=OrderStatus.nouvelle,
            total_cents=500,
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.commit()


@pytest.mark.asyncio
async def test_payments_table_exists_and_is_empty_after_schema(db_session):
    count = (
        await db_session.execute(select(Payment))
    ).scalars().all()
    assert count == []
    assert "order_id" in Payment.__table__.columns.keys()
    assert "amount_cents" in Payment.__table__.columns.keys()


@pytest.mark.asyncio
async def test_order_item_snapshots_unit_price_cents(db_session):
    restaurant = Restaurant(name="Chicken Street Paris", slug="chicken-street-paris")
    db_session.add(restaurant)
    await db_session.flush()
    table = Table(restaurant_id=restaurant.id, label="14", public_token=uuid.uuid4().hex)
    category = Category(restaurant_id=restaurant.id, name="Burgers", sort_order=1)
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
    )
    db_session.add(order)
    await db_session.flush()

    item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        quantity=1,
        unit_price_cents=1250,
    )
    db_session.add(item)
    await db_session.commit()

    loaded = (await db_session.execute(select(OrderItem))).scalar_one()
    assert loaded.unit_price_cents == 1250


@pytest.mark.asyncio
async def test_option_and_order_item_option_tables_exist(db_session):
    restaurant = Restaurant(name="Chicken Street Paris", slug="chicken-street-paris")
    db_session.add(restaurant)
    await db_session.flush()
    category = Category(restaurant_id=restaurant.id, name="Burgers", sort_order=1)
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
    await db_session.commit()

    assert option.price_delta_cents == 100
    assert OrderItemOption.__tablename__ == "order_item_options"
