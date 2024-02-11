from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

from pix.app import AppGraph
from pix.model.image import ImageRepo

tags_router = APIRouter()


class ListTagsResultItem(BaseModel):
    tag: str
    image_count: int


@tags_router.get("/api/tags")
def list_tags(q: Optional[str] = None):
    image_repo = AppGraph.get_instance(ImageRepo)
    tags = image_repo.list_all_tags_with_count(q)
    tags.sort(key=lambda tc: tc[1], reverse=True)
    return [ListTagsResultItem(tag=tag, image_count=count) for tag, count in tags]
