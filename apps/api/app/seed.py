"""Seed Chicken Street Paris demo data for one real-restaurant MVP."""

from __future__ import annotations

import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AdminUser,
    Category,
    Option,
    OptionGroup,
    Product,
    Restaurant,
    Table,
)

DEMO_SLUG = "chicken-street-paris"
# Placeholder hash only — admin auth lands in S2. Not a real password.
DEMO_ADMIN_EMAIL = "admin@nh.local"
DEMO_ADMIN_PASSWORD_HASH = "s1-placeholder-not-for-login"


def _token() -> str:
    return secrets.token_urlsafe(16)


async def seed_demo(session: AsyncSession) -> Restaurant:
    existing = (
        await session.execute(select(Restaurant).where(Restaurant.slug == DEMO_SLUG))
    ).scalar_one_or_none()
    if existing is not None:
        return existing

    restaurant = Restaurant(name="Chicken Street Paris", slug=DEMO_SLUG)
    session.add(restaurant)
    await session.flush()

    session.add(
        AdminUser(email=DEMO_ADMIN_EMAIL, password_hash=DEMO_ADMIN_PASSWORD_HASH)
    )

    burgers = Category(restaurant_id=restaurant.id, name="Burgers", sort_order=1)
    sides = Category(restaurant_id=restaurant.id, name="Accompagnements", sort_order=2)
    drinks = Category(restaurant_id=restaurant.id, name="Boissons", sort_order=3)
    session.add_all([burgers, sides, drinks])
    await session.flush()

    chicken_burger = Product(
        restaurant_id=restaurant.id,
        category_id=burgers.id,
        name="Chicken Burger",
        description="Pain, filet de poulet, salade",
        price_cents=1250,
        available=True,
        sort_order=1,
    )
    frites = Product(
        restaurant_id=restaurant.id,
        category_id=sides.id,
        name="Frites",
        description="Portion classique",
        price_cents=350,
        available=True,
        sort_order=1,
    )
    coca = Product(
        restaurant_id=restaurant.id,
        category_id=drinks.id,
        name="Coca-Cola",
        description="33 cl",
        price_cents=300,
        available=True,
        sort_order=1,
    )
    session.add_all([chicken_burger, frites, coca])
    await session.flush()

    extras = OptionGroup(
        product_id=chicken_burger.id,
        name="Suppléments",
        required=False,
        min_select=0,
        max_select=3,
    )
    session.add(extras)
    await session.flush()
    session.add(Option(option_group_id=extras.id, name="fromage", price_delta_cents=100))

    session.add(
        Table(
            restaurant_id=restaurant.id,
            label="14",
            public_token=_token(),
            active=True,
        )
    )
    await session.flush()
    return restaurant


async def run_seed() -> None:
    from app.db import SessionLocal

    async with SessionLocal() as session:
        restaurant = await seed_demo(session)
        await session.commit()
        print(f"Seeded restaurant: {restaurant.name} ({restaurant.slug})")


if __name__ == "__main__":
    import asyncio

    asyncio.run(run_seed())
