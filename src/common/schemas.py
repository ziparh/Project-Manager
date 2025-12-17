from pydantic import BaseModel, Field
from typing import Generic, TypeVar, Literal, Any, Sequence


class BasePaginationParams(BaseModel):
    """Base query parameters for pagination"""

    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(20, ge=1, le=100, description="Number of elements on page")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


class BasePaginationMeta(BaseModel):
    """Base pagination metadata in response"""

    total: int = Field(description="Total number of elements")
    page: int = Field(description="Current page number (1-based)")
    size: int = Field(description="Elements per page")

    @property
    def pages(self) -> int:
        """Number of pages"""
        if self.size <= 0:
            return 1
        return (self.total + self.size - 1) // self.limit

    @property
    def has_next(self) -> bool:
        """Is there a next page"""
        return self.page < self.pages

    @property
    def has_previous(self) -> bool:
        """Is there a previous page"""
        return self.page > 1


T = TypeVar("T")


class BasePaginationResponse(BaseModel, Generic[T]):
    """Base response with pagination"""

    items: Sequence[T]
    pagination: BasePaginationMeta


class BaseSortingParams(BaseModel):
    """Base query parameters for sorting"""

    sort_by: Any
    order: Literal["asc", "desc"] = Field("asc", description="Sort order")
