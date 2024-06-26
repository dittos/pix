import datetime
from typing import List, Optional, Union
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from pix.app import AppGraph
from pix.embeddings.clip import ClipEmbedding
from pix.autotagger.custom import CustomAutotagger
from pix.embedding_index import EmbeddingIndexManager, MultiEmbeddingIndexManager
from pix.model.face_cluster import FaceClusterRepo
from pix.model.image import Image, ImageRepo, ImageTag


images_router = APIRouter()


class ImageDto(BaseModel):
    id: str
    local_filename: str
    collected_at: datetime.datetime

    source_url: Union[str, None]
    tweet_id: Union[str, None]
    tweet_username: Union[str, None]

    tags: Union[List[ImageTag], None]
    manual_tags: Union[List[ImageTag], None]
    embedding_types: List[str]
    # embedding: Union[Vector, None] = None
    # faces: Union[List[ImageFace], None] = None

    @staticmethod
    def from_doc(image: Image):
        fields = image.model_dump()
        embedding_types = []
        if image.embedding:
            embedding_types.append("default")
        if image.embeddings:
            embedding_types.extend(image.embeddings.keys())
        fields["embedding_types"] = embedding_types
        return ImageDto.model_validate(fields)


class ListImagesResult(BaseModel):
    data: List[ImageDto]
    count: int
    has_next_page: bool


@images_router.get("/api/images")
def list_images(page: int = 1, tag: Optional[str] = None) -> ListImagesResult:
    limit = 20
    offset = (page - 1) * limit
    image_repo = AppGraph.get_instance(ImageRepo)
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


@images_router.get("/api/images/search")
def search_images(q: str, limit: int = 100):
    image_repo = AppGraph.get_instance(ImageRepo)
    index = AppGraph.get_instance(MultiEmbeddingIndexManager).get_manager("clip")
    embedding = AppGraph.get_instance(ClipEmbedding)
    embedding.load_model()

    result = []
    for sim_id, score in index.search(embedding.encode_text(q), limit):
        sim_image = image_repo.get(sim_id)
        if sim_image is None: continue

        result.append({
            "image": ImageDto.from_doc(sim_image),
            "score": score,
        })
    
    return result


@images_router.get("/api/images/{image_id}")
def get_image(image_id: str):
    image_repo = AppGraph.get_instance(ImageRepo)
    image = image_repo.get(image_id)
    if image is None:
        raise HTTPException(404)
    
    return ImageDto.from_doc(image)


@images_router.get("/api/images/{image_id}/similar")
def list_similar_images(image_id: str, count: int = 10, embedding_type: str = "default"):
    image_repo = AppGraph.get_instance(ImageRepo)
    image = image_repo.get(image_id)
    if image is None:
        raise HTTPException(404)
    
    if embedding_type == "default":
        emb = image.embedding
    else:
        emb = image.embeddings.get(embedding_type)
        
    if not emb:
        return []

    index = AppGraph.get_instance(MultiEmbeddingIndexManager).get_manager(embedding_type)
    result = []
    for sim_id, score in index.search(emb.to_numpy(), count + 1):
        if sim_id == image_id: continue
        sim_image = image_repo.get(sim_id)
        if sim_image is None: continue

        result.append({
            "image": ImageDto.from_doc(sim_image),
            "score": score,
        })
    
    return result


@images_router.get("/api/images/{image_id}/faces")
def list_image_faces(image_id: str):
    image_repo = AppGraph.get_instance(ImageRepo)
    image = image_repo.get(image_id)
    if image is None:
        raise HTTPException(404)
    
    if not image.faces:
        return []

    fc_repo = AppGraph.get_instance(FaceClusterRepo)
    result = []
    for i, face in enumerate(image.faces):
        fc = fc_repo.get_by_face_ref(image.id, i)
        result.append({
            "index": i,
            "local_filename": face.local_filename,
            "face_cluster_id": fc.id if fc else None,
            "face_cluster_label": fc.label if fc else None,
        })
    
    return result


class SetImageManualTagsRequest(BaseModel):
    manual_tags: List[ImageTag]


@images_router.put("/api/images/{image_id}/manual-tags")
def set_image_manual_tags(image_id: str, request: SetImageManualTagsRequest):
    image_repo = AppGraph.get_instance(ImageRepo)
    image = image_repo.get(image_id)
    if image is None:
        raise HTTPException(404)
    
    seen_tag_names = set(tag.tag for tag in image.tags)
    for tag in request.manual_tags:
        if tag.tag in seen_tag_names:
            raise HTTPException(400, f"Already added tag: {tag.tag}")
        seen_tag_names.add(tag.tag)

    image.manual_tags = request.manual_tags
    image_repo.update(image)

    return ImageDto.from_doc(image)


@images_router.get("/api/images/{image_id}/custom-autotags")
def get_image_custom_autotags(image_id: str):
    image_repo = AppGraph.get_instance(ImageRepo)
    image = image_repo.get(image_id)
    if image is None:
        raise HTTPException(404)

    if image.embedding is None:
        return []
    
    autotagger = AppGraph.get_instance(CustomAutotagger)
    autotagger.load_model()

    return autotagger.extract(image.embedding.to_numpy())
