from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_session
from app.models import Category, OptionGroup, Product, Restaurant, Table
from app.schemas import (
    PublicCategoryOut,
    PublicMenuOut,
    PublicOptionOut,
    PublicProductOut,
    PublicRestaurantOut,
    PublicTableOut,
)

router = APIRouter(tags=["public"])


@router.get("/t/{token}/menu", response_model=PublicMenuOut)
async def get_menu_by_table_token(
    token: str,
    session: AsyncSession = Depends(get_session),
):
    table = (
        await session.execute(
            select(Table).where(Table.public_token == token, Table.active.is_(True))
        )
    ).scalar_one_or_none()
    if table is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Table not found")

    restaurant = await session.get(Restaurant, table.restaurant_id)
    if restaurant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")

    categories = (
        await session.execute(
            select(Category)
            .where(Category.restaurant_id == restaurant.id, Category.active.is_(True))
            .order_by(Category.sort_order, Category.name)
        )
    ).scalars().all()

    products = (
        await session.execute(
            select(Product)
            .where(
                Product.restaurant_id == restaurant.id,
                Product.available.is_(True),
            )
            .options(
                selectinload(Product.option_groups).selectinload(OptionGroup.options)
            )
            .order_by(Product.sort_order, Product.name)
        )
    ).scalars().all()

    products_by_category: dict = {}
    for product in products:
        products_by_category.setdefault(product.category_id, []).append(product)

    public_categories: list[PublicCategoryOut] = []
    for category in categories:
        public_products: list[PublicProductOut] = []
        for product in products_by_category.get(category.id, []):
            options: list[PublicOptionOut] = []
            for group in product.option_groups:
                for option in group.options:
                    options.append(
                        PublicOptionOut(
                            id=option.id,
                            name=option.name,
                            price_delta_cents=option.price_delta_cents,
                            group_name=group.name,
                            required=group.required,
                            min_select=group.min_select,
                            max_select=group.max_select,
                        )
                    )
            public_products.append(
                PublicProductOut(
                    id=product.id,
                    name=product.name,
                    description=product.description,
                    price_cents=product.price_cents,
                    photo_url=product.photo_url,
                    options=options,
                )
            )
        if public_products:
            public_categories.append(
                PublicCategoryOut(
                    id=category.id,
                    name=category.name,
                    sort_order=category.sort_order,
                    products=public_products,
                )
            )

    return PublicMenuOut(
        restaurant=PublicRestaurantOut(
            id=restaurant.id,
            name=restaurant.name,
            currency=restaurant.currency,
        ),
        table=PublicTableOut(label=table.label, public_token=table.public_token),
        categories=public_categories,
    )
