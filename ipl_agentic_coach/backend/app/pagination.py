"""Pagination and filtering utilities."""
from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Query

T = TypeVar('T')


class PaginationParams(BaseModel):
    """Pagination parameters."""
    skip: int = 0
    limit: int = 50
    sort_by: Optional[str] = None
    sort_order: str = "asc"  # asc or desc

    def __init__(self, **data):
        super().__init__(**data)
        # Enforce limits
        self.skip = max(0, self.skip)
        self.limit = min(max(1, self.limit), 1000)  # 1-1000 items per page


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated response."""
    items: List[T]
    total: int
    skip: int
    limit: int
    pages: int

    class Config:
        arbitrary_types_allowed = True


def paginate(
    query: Query,
    params: PaginationParams,
    count: Optional[int] = None
) -> tuple[List, int]:
    """Apply pagination to query."""
    total = count if count is not None else query.count()
    items = query.offset(params.skip).limit(params.limit).all()
    return items, total


def get_pagination_metadata(total: int, params: PaginationParams) -> dict:
    """Get pagination metadata."""
    pages = (total + params.limit - 1) // params.limit
    return {
        "total": total,
        "skip": params.skip,
        "limit": params.limit,
        "pages": pages,
        "current_page": (params.skip // params.limit) + 1,
        "has_next": params.skip + params.limit < total,
        "has_prev": params.skip > 0,
    }
