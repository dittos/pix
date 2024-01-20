from contextlib import AbstractContextManager, nullcontext
from dataclasses import dataclass
from typing import Any, Optional, Protocol, List

from pix.model.tweet import Tweet


@dataclass
class PaginatedResult:
    tweets: List[Tweet]
    pagination_state: Any


class TwitterDownloader(Protocol):
    def open(self) -> AbstractContextManager:
        return nullcontext()

    def get_favorites(self, username: str, pagination_state: Optional[Any] = None) -> PaginatedResult: ...
