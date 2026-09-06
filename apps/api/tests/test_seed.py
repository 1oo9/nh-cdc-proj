"""Seed behaviour: one real restaurant demo for NH."""

from __future__ import annotations

import pytest
from sqlalchemy import func, select

from app.models import Category, Product, Restaurant, Table
from app.seed import seed_demo


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
    assert len(categories) >= 2

    products = (
        await db_session.execute(
            select(Product).where(Product.restaurant_id == restaurant.id)
        )
    ).scalars().all()
    assert len(products) >= 3
    assert all(isinstance(p.price_cents, int) for p in products)

    table = (
        await db_session.execute(
            select(Table).where(
                Table.restaurant_id == restaurant.id,
                Table.label == "14",
            )
        )
    ).scalar_one()
    assert table.public_token
    assert len(table.public_token) >= 16
    assert table.public_token != "14"


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
