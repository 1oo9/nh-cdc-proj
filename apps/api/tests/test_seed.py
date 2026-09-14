"""Seed behaviour: one real restaurant demo for NH."""

from __future__ import annotations

import pytest
from sqlalchemy import func, select

from app.models import Category, Option, Product, Restaurant, Table
from app.seed import DEMO_TABLE_LABELS, seed_demo


@pytest.mark.asyncio
async def test_seed_creates_chicken_street_paris_with_menu_and_table(db_session):
    await seed_demo(db_session)
    await db_session.commit()

    restaurant = (
        await db_session.execute(
            select(Restaurant).where(Restaurant.slug == "chicken-street-paris")
        )
    ).scalar_one()
    assert restaurant.name == "Chicken Street Paris"

    categories = (
        await db_session.execute(
            select(Category).where(Category.restaurant_id == restaurant.id)
        )
    ).scalars().all()
    assert len(categories) >= 3
    names = {c.name for c in categories}
    assert "Burgers" in names
    assert "Accompagnements" in names
    assert "Boissons" in names

    products = (
        await db_session.execute(
            select(Product).where(Product.restaurant_id == restaurant.id)
        )
    ).scalars().all()
    assert len(products) >= 6
    assert all(isinstance(p.price_cents, int) for p in products)
    product_names = {p.name for p in products}
    assert "Chicken Burger" in product_names
    assert "Street Burger" in product_names
    assert "Tenders" in product_names

    options = (await db_session.execute(select(Option))).scalars().all()
    option_names = {o.name for o in options}
    assert "fromage" in option_names
    assert "bacon" in option_names

    tables = (
        await db_session.execute(
            select(Table).where(Table.restaurant_id == restaurant.id)
        )
    ).scalars().all()
    labels = sorted(t.label for t in tables)
    assert labels == sorted(DEMO_TABLE_LABELS)
    for table in tables:
        assert table.public_token
        assert len(table.public_token) >= 16
        assert table.public_token != table.label


@pytest.mark.asyncio
async def test_seed_is_idempotent(db_session):
    await seed_demo(db_session)
    await db_session.commit()
    await seed_demo(db_session)
    await db_session.commit()

    count = (
        await db_session.execute(select(func.count()).select_from(Restaurant))
    ).scalar_one()
    assert count == 1

    table_count = (
        await db_session.execute(select(func.count()).select_from(Table))
    ).scalar_one()
    assert table_count == len(DEMO_TABLE_LABELS)


@pytest.mark.asyncio
async def test_seed_fills_missing_demo_tables_on_rerun(db_session):
    await seed_demo(db_session)
    await db_session.commit()

    # Simulate an older seed that only had table 14.
    extras = (
        await db_session.execute(select(Table).where(Table.label.in_(["12", "13"])))
    ).scalars().all()
    for table in extras:
        await db_session.delete(table)
    await db_session.commit()

    await seed_demo(db_session)
    await db_session.commit()

    labels = (
        await db_session.execute(select(Table.label).order_by(Table.label))
    ).scalars().all()
    assert list(labels) == sorted(DEMO_TABLE_LABELS)
