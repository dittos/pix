from typing import Optional
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from pix.app import create_graph
from pix.config import Settings
from pix.model.image import ImageRepo


app = FastAPI()
graph = create_graph(debug=True)
app.mount("/images", StaticFiles(directory=graph.get_instance(Settings).images_dir), name="images")


class ListTagsResultItem(BaseModel):
    tag: str
    image_count: int


@app.get("/api/tags")
def list_tags(q: Optional[str] = None):
    image_repo = graph.get_instance(ImageRepo)
    tags = image_repo.list_all_tags_with_count(q)
    tags.sort(key=lambda tc: tc[1], reverse=True)
    return [ListTagsResultItem(tag=tag, image_count=count) for tag, count in tags]


@app.get("/api/images")
def list_images(page: int = 1, tag: Optional[str] = None):
    limit = 20
    offset = (page - 1) * limit
    image_repo = graph.get_instance(ImageRepo)
    if tag:
        images = image_repo.list_by_tag_collected_at_desc(tag, offset, limit + 1)
        count = image_repo.count_by_tag(tag)
    else:
        images = image_repo.list_by_collected_at_desc(offset, limit + 1)
        count = image_repo.count()
    has_next_page = len(images) > limit
    images = images[:limit]
    return {
        "data": images,
        "count": count,
        "has_next_page": has_next_page,
    }
