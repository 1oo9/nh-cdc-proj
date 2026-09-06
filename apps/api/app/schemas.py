from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RestaurantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    currency: str
    timezone: str


class RestaurantUpdate(BaseModel):
    name: str | None = None
    currency: str | None = None
    timezone: str | None = None


class CategoryCreate(BaseModel):
    name: str
    sort_order: int = 0
    active: bool = True


class CategoryUpdate(BaseModel):
    name: str | None = None
    sort_order: int | None = None
    active: bool | None = None


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    restaurant_id: UUID
    name: str
    sort_order: int
    active: bool


class ProductCreate(BaseModel):
    category_id: UUID
    name: str
    description: str | None = None
    price_cents: int = Field(ge=0)
    photo_url: str | None = None
    available: bool = True
    sort_order: int = 0


class ProductUpdate(BaseModel):
    category_id: UUID | None = None
    name: str | None = None
    description: str | None = None
    price_cents: int | None = Field(default=None, ge=0)
    photo_url: str | None = None
    available: bool | None = None
    sort_order: int | None = None


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    restaurant_id: UUID
    category_id: UUID
    name: str
    description: str | None
    price_cents: int
    photo_url: str | None
    available: bool
    sort_order: int


class OptionGroupCreate(BaseModel):
    name: str
    required: bool = False
    min_select: int = 0
    max_select: int = 1


class OptionGroupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    name: str
    required: bool
    min_select: int
    max_select: int


class OptionCreate(BaseModel):
    name: str
    price_delta_cents: int = 0


class OptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    option_group_id: UUID
    name: str
    price_delta_cents: int


class TableCreate(BaseModel):
    label: str
    active: bool = True


class TableOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    restaurant_id: UUID
    label: str
    public_token: str
    active: bool


class PublicRestaurantOut(BaseModel):
    id: UUID
    name: str
    currency: str


class PublicTableOut(BaseModel):
    label: str
    public_token: str


class PublicOptionOut(BaseModel):
    id: UUID
    name: str
    price_delta_cents: int
    group_name: str
    required: bool
    min_select: int
    max_select: int


class PublicProductOut(BaseModel):
    id: UUID
    name: str
    description: str | None
    price_cents: int
    photo_url: str | None
    options: list[PublicOptionOut]


class PublicCategoryOut(BaseModel):
    id: UUID
    name: str
    sort_order: int
    products: list[PublicProductOut]


class PublicMenuOut(BaseModel):
    restaurant: PublicRestaurantOut
    table: PublicTableOut
    categories: list[PublicCategoryOut]
