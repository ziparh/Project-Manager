from dataclasses import dataclass
from typing import Literal


@dataclass
class PaginationDto:
    size: int
    offset: int


@dataclass
class SortingDto:
    sort_by: str
    order: Literal["asc", "desc"] = "asc"
