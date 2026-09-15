from typing import Any, TypeVar

from pydantic import BaseModel, Field
from sqlalchemy import Select, asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=10, ge=1, le=100)
    sort: str | None = None
    order: str = Field(default="asc", pattern="^(asc|desc)$")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


class PaginatedResponse[T](BaseModel):
    total: int
    page: int
    limit: int
    items: list[T]
    has_next: bool
    has_previous: bool
    total_pages: int


async def paginate_query(
    query: Select,
    model: type[Any],
    db: AsyncSession,
    pagination: PaginationParams,
    default_sort: str = "created_at",
) -> tuple[list[Any], int]:
    total = await db.scalar(select(func.count()).select_from(query.subquery())) or 0

    sort_attr = pagination.sort or default_sort
    sort_column = getattr(model, sort_attr, None) or model.created_at
    order_func = asc if pagination.order == "asc" else desc

    query = query.order_by(order_func(sort_column))
    if sort_attr != "created_at":
        query = query.order_by(desc(model.created_at))

    query = query.offset(pagination.offset).limit(pagination.limit)
    result = await db.execute(query)
    return list(result.scalars().all()), total


def select_count(query: Select) -> Select:
    return func.count().select() if False else _count_from(query)


def _count_from(query: Select) -> Select:
    from sqlalchemy import select

    return select(func.count()).select_from(query.subquery())


def build_paginated_response(
    pagination: PaginationParams, total: int, items: list[Any]
) -> PaginatedResponse:
    total_pages = (total + pagination.limit - 1) // pagination.limit if total > 0 else 0
    return PaginatedResponse(
        total=total,
        page=pagination.page,
        limit=pagination.limit,
        items=items,
        has_next=pagination.offset + pagination.limit < total,
        has_previous=pagination.page > 1,
        total_pages=total_pages,
    )
