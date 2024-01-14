from dataclasses import dataclass
from typing import Generic, TypeVar

from pydantic import BaseModel


T = TypeVar("T", bound=BaseModel)


@dataclass
class Doc(Generic[T]):
    id: str
    content: T
