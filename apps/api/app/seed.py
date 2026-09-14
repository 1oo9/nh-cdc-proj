"""Seed Chicken Street Paris demo data for one real-restaurant MVP."""

from __future__ import annotations

import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import hash_password
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
DEMO_ADMIN_EMAIL = "admin@nh.example"
DEMO_ADMIN_PASSWORD = "nh-admin"
DEMO_TABLE_LABELS = ("12", "13", "14")


def _token() -> str:
    return secrets.token_urlsafe(16)


async def _ensure_admin(session: AsyncSession) -> None:
    admin = (
        await session.execute(select(AdminUser).where(AdminUser.email == DEMO_ADMIN_EMAIL))
    ).scalar_one_or_none()
    password_hash = hash_password(DEMO_ADMIN_PASSWORD)
    if admin is None:
        session.add(AdminUser(email=DEMO_ADMIN_EMAIL, password_hash=password_hash))
    else:
        admin.password_hash = password_hash


async def _ensure_category(
    session: AsyncSession, restaurant_id, name: str, sort_order: int
) -> Category:
    category = (
        await session.execute(
            select(Category).where(
                Category.restaurant_id == restaurant_id,
                Category.name == name,
            )
        )
    ).scalar_one_or_none()
    if category is None:
        category = Category(
            restaurant_id=restaurant_id,
            name=name,
            sort_order=sort_order,
            active=True,
        )
        session.add(category)
        await session.flush()
    return category


async def _ensure_product(
    session: AsyncSession,
    *,
    restaurant_id,
    category_id,
    name: str,
    description: str,
    price_cents: int,
    sort_order: int,
) -> Product:
    product = (
        await session.execute(
            select(Product).where(
                Product.restaurant_id == restaurant_id,
                Product.name == name,
            )
        )
    ).scalar_one_or_none()
    if product is None:
        product = Product(
            restaurant_id=restaurant_id,
            category_id=category_id,
            name=name,
            description=description,
            price_cents=price_cents,
            available=True,
            sort_order=sort_order,
        )
        session.add(product)
        await session.flush()
    return product


async def _ensure_option(
    session: AsyncSession, product_id, group_name: str, option_name: str, price_delta_cents: int
) -> None:
    group = (
        await session.execute(
            select(OptionGroup).where(
                OptionGroup.product_id == product_id,
                OptionGroup.name == group_name,
            )
        )
    ).scalar_one_or_none()
    if group is None:
        group = OptionGroup(
            product_id=product_id,
            name=group_name,
            required=False,
            min_select=0,
            max_select=3,
        )
        session.add(group)
        await session.flush()

    existing = (
        await session.execute(
            select(Option).where(
                Option.option_group_id == group.id,
                Option.name == option_name,
            )
        )
    ).scalar_one_or_none()
    if existing is None:
        session.add(
            Option(
                option_group_id=group.id,
                name=option_name,
                price_delta_cents=price_delta_cents,
            )
        )


async def _ensure_tables(session: AsyncSession, restaurant_id) -> None:
    for label in DEMO_TABLE_LABELS:
        table = (
            await session.execute(
                select(Table).where(
                    Table.restaurant_id == restaurant_id,
                    Table.label == label,
                )
            )
        ).scalar_one_or_none()
        if table is None:
            session.add(
                Table(
                    restaurant_id=restaurant_id,
                    label=label,
                    public_token=_token(),
                    active=True,
                )
            )


async def _ensure_menu(session: AsyncSession, restaurant: Restaurant) -> None:
    burgers = await _ensure_category(session, restaurant.id, "Burgers", 1)
    sides = await _ensure_category(session, restaurant.id, "Accompagnements", 2)
    drinks = await _ensure_category(session, restaurant.id, "Boissons", 3)

    chicken = await _ensure_product(
        session,
        restaurant_id=restaurant.id,
        category_id=burgers.id,
        name="Chicken Burger",
        description="Pain brioché, filet de poulet croustillant, salade",
        price_cents=1250,
        sort_order=1,
    )
    street = await _ensure_product(
        session,
        restaurant_id=restaurant.id,
        category_id=burgers.id,
        name="Street Burger",
        description="Double filet, sauce street, oignons frits",
        price_cents=1450,
        sort_order=2,
    )
    await _ensure_product(
        session,
        restaurant_id=restaurant.id,
        category_id=burgers.id,
        name="Cheese Chicken",
        description="Filet de poulet, cheddar fondu",
        price_cents=1350,
        sort_order=3,
    )
    await _ensure_product(
        session,
        restaurant_id=restaurant.id,
        category_id=sides.id,
        name="Frites",
        description="Portion classique",
        price_cents=350,
        sort_order=1,
    )
    await _ensure_product(
        session,
        restaurant_id=restaurant.id,
        category_id=sides.id,
        name="Tenders",
        description="4 pièces de poulet pané",
        price_cents=650,
        sort_order=2,
    )
    await _ensure_product(
        session,
        restaurant_id=restaurant.id,
        category_id=drinks.id,
        name="Coca-Cola",
        description="33 cl",
        price_cents=300,
        sort_order=1,
    )
    await _ensure_product(
        session,
        restaurant_id=restaurant.id,
        category_id=drinks.id,
        name="Eau",
        description="50 cl",
        price_cents=200,
        sort_order=2,
    )

    for product in (chicken, street):
        await _ensure_option(session, product.id, "Suppléments", "fromage", 100)
        await _ensure_option(session, product.id, "Suppléments", "bacon", 150)

    await session.flush()


async def seed_demo(session: AsyncSession) -> Restaurant:
    restaurant = (
        await session.execute(select(Restaurant).where(Restaurant.slug == DEMO_SLUG))
    ).scalar_one_or_none()
    if restaurant is None:
        restaurant = Restaurant(name="Chicken Street Paris", slug=DEMO_SLUG)
        session.add(restaurant)
        await session.flush()

    await _ensure_admin(session)
    await _ensure_menu(session, restaurant)
    await _ensure_tables(session, restaurant.id)
    await session.flush()
    return restaurant


async def run_seed() -> None:
    from app.db import SessionLocal

    async with SessionLocal() as session:
        restaurant = await seed_demo(session)
        await session.commit()
        print(f"Seeded restaurant: {restaurant.name} ({restaurant.slug})")
        print(f"Admin login: {DEMO_ADMIN_EMAIL} / {DEMO_ADMIN_PASSWORD}")
        print(f"Demo tables: {', '.join(DEMO_TABLE_LABELS)}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(run_seed())
