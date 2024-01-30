import datetime
from typing import List, Optional, Union
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from pix.app import create_graph
from pix.config import Settings
from pix.embedding_index import EmbeddingIndexManager
from pix.model.image import Image, ImageRepo, ImageTag
from pixdb.doc import Doc


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


class ImageDto(BaseModel):
    id: str
    local_filename: str
    collected_at: datetime.datetime

    source_url: Union[str, None]
    tweet_id: Union[str, None]
    tweet_username: Union[str, None]

    tags: Union[List[ImageTag], None]
    # embedding: Union[Vector, None] = None
    # faces: Union[List[ImageFace], None] = None

    @staticmethod
    def from_doc(doc: Doc[Image]):
        fields = doc.content.model_dump()
        fields["id"] = doc.id
        return ImageDto.model_validate(fields)


class ListImagesResult(BaseModel):
    data: List[ImageDto]
    count: int
    has_next_page: bool


@app.get("/api/images")
def list_images(page: int = 1, tag: Optional[str] = None) -> ListImagesResult:
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
    return ListImagesResult(
        data=list(map(ImageDto.from_doc, images)),
        count=count,
        has_next_page=has_next_page,
    )


@app.get("/api/images/{image_id}/similar")
def list_similar_images(image_id: str, count: int = 5):
    image_repo = graph.get_instance(ImageRepo)
    image = image_repo.get(image_id)
    if image is None:
        raise HTTPException(404)
    
    if image.content.embedding is None:
        return []

    index = graph.get_instance(EmbeddingIndexManager)
    result = []
    for sim_id, score in index.search(image.content.embedding.to_numpy(), count + 1):
        if sim_id == image_id: continue
        sim_image = image_repo.get(sim_id)
        if sim_image is None: continue

        result.append({
            "image": ImageDto.from_doc(sim_image),
            "score": score,
        })
    
    return result
