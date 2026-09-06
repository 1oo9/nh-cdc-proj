from __future__ import annotations

import secrets
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import (
    create_access_token,
    get_current_admin,
    hash_password,
    verify_password,
)
from app.db import get_session
from app.models import (
    AdminUser,
    Category,
    Option,
    OptionGroup,
    Product,
    Restaurant,
    Table,
)
from app.qr import qr_png_bytes
from app.schemas import (
    CategoryCreate,
    CategoryOut,
    CategoryUpdate,
    LoginRequest,
    OptionCreate,
    OptionGroupCreate,
    OptionGroupOut,
    OptionOut,
    ProductCreate,
    ProductOut,
    ProductUpdate,
    RestaurantOut,
    RestaurantUpdate,
    TableCreate,
    TableOut,
    TokenResponse,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, session: AsyncSession = Depends(get_session)):
    admin = (
        await session.execute(select(AdminUser).where(AdminUser.email == body.email))
    ).scalar_one_or_none()
    if admin is None or not verify_password(body.password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    return TokenResponse(access_token=create_access_token(subject=str(admin.id)))


@router.get("/restaurants", response_model=list[RestaurantOut])
async def list_restaurants(
    _: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    rows = (await session.execute(select(Restaurant).order_by(Restaurant.name))).scalars().all()
    return rows


@router.patch("/restaurants/{restaurant_id}", response_model=RestaurantOut)
async def update_restaurant(
    restaurant_id: UUID,
    body: RestaurantUpdate,
    _: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    restaurant = await session.get(Restaurant, restaurant_id)
    if restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(restaurant, field, value)
    await session.commit()
    await session.refresh(restaurant)
    return restaurant


@router.get("/restaurants/{restaurant_id}/categories", response_model=list[CategoryOut])
async def list_categories(
    restaurant_id: UUID,
    _: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    rows = (
        await session.execute(
            select(Category)
            .where(Category.restaurant_id == restaurant_id)
            .order_by(Category.sort_order, Category.name)
        )
    ).scalars().all()
    return rows


@router.post(
    "/restaurants/{restaurant_id}/categories",
    response_model=CategoryOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_category(
    restaurant_id: UUID,
    body: CategoryCreate,
    _: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    if await session.get(Restaurant, restaurant_id) is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    category = Category(restaurant_id=restaurant_id, **body.model_dump())
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return category


@router.patch("/categories/{category_id}", response_model=CategoryOut)
async def update_category(
    category_id: UUID,
    body: CategoryUpdate,
    _: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    category = await session.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(category, field, value)
    await session.commit()
    await session.refresh(category)
    return category


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: UUID,
    _: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    category = await session.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    await session.delete(category)
    await session.commit()


@router.get("/restaurants/{restaurant_id}/products", response_model=list[ProductOut])
async def list_products(
    restaurant_id: UUID,
    _: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    rows = (
        await session.execute(
            select(Product)
            .where(Product.restaurant_id == restaurant_id)
            .order_by(Product.sort_order, Product.name)
        )
    ).scalars().all()
    return rows


@router.post(
    "/restaurants/{restaurant_id}/products",
    response_model=ProductOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_product(
    restaurant_id: UUID,
    body: ProductCreate,
    _: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    if await session.get(Restaurant, restaurant_id) is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    category = await session.get(Category, body.category_id)
    if category is None or category.restaurant_id != restaurant_id:
        raise HTTPException(status_code=400, detail="Invalid category")
    product = Product(restaurant_id=restaurant_id, **body.model_dump())
    session.add(product)
    await session.commit()
    await session.refresh(product)
    return product


@router.patch("/products/{product_id}", response_model=ProductOut)
async def update_product(
    product_id: UUID,
    body: ProductUpdate,
    _: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    product = await session.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    data = body.model_dump(exclude_unset=True)
    if "category_id" in data:
        category = await session.get(Category, data["category_id"])
        if category is None or category.restaurant_id != product.restaurant_id:
            raise HTTPException(status_code=400, detail="Invalid category")
    for field, value in data.items():
        setattr(product, field, value)
    await session.commit()
    await session.refresh(product)
    return product


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: UUID,
    _: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    product = await session.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    await session.delete(product)
    await session.commit()


@router.post(
    "/products/{product_id}/option-groups",
    response_model=OptionGroupOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_option_group(
    product_id: UUID,
    body: OptionGroupCreate,
    _: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    if await session.get(Product, product_id) is None:
        raise HTTPException(status_code=404, detail="Product not found")
    group = OptionGroup(product_id=product_id, **body.model_dump())
    session.add(group)
    await session.commit()
    await session.refresh(group)
    return group


@router.post(
    "/option-groups/{group_id}/options",
    response_model=OptionOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_option(
    group_id: UUID,
    body: OptionCreate,
    _: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    if await session.get(OptionGroup, group_id) is None:
        raise HTTPException(status_code=404, detail="Option group not found")
    option = Option(option_group_id=group_id, **body.model_dump())
    session.add(option)
    await session.commit()
    await session.refresh(option)
    return option


@router.get("/restaurants/{restaurant_id}/tables", response_model=list[TableOut])
async def list_tables(
    restaurant_id: UUID,
    _: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    rows = (
        await session.execute(
            select(Table)
            .where(Table.restaurant_id == restaurant_id)
            .order_by(Table.label)
        )
    ).scalars().all()
    return rows


@router.post(
    "/restaurants/{restaurant_id}/tables",
    response_model=TableOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_table(
    restaurant_id: UUID,
    body: TableCreate,
    _: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    if await session.get(Restaurant, restaurant_id) is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    table = Table(
        restaurant_id=restaurant_id,
        label=body.label,
        public_token=secrets.token_urlsafe(16),
        active=body.active,
    )
    session.add(table)
    await session.commit()
    await session.refresh(table)
    return table


@router.get("/tables/{table_id}/qr.png")
async def download_table_qr(
    table_id: UUID,
    _: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    table = await session.get(Table, table_id)
    if table is None:
        raise HTTPException(status_code=404, detail="Table not found")
    return Response(
        content=qr_png_bytes(table.public_token),
        media_type="image/png",
        headers={
            "Content-Disposition": f'attachment; filename="table-{table.label}-qr.png"'
        },
    )
