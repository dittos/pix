import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Dict, List, Literal, Optional, Union
from fastapi import APIRouter, HTTPException
import numpy as np
from pydantic import BaseModel
import requests

from pix.app import AppGraph
from pix.autotagger.wd import WdAutotagger
from pix.embeddings.clip import ClipEmbedding
from pix.autotagger.custom import CustomAutotagger
from pix.embedding_index import MultiEmbeddingIndexManager
from pix.embeddings.csd import CsdEmbedding
from pix.model.face_cluster import FaceClusterRepo
from pix.model.image import Image, ImageRepo, ImageTag, TagQuery, TagQueryTermFace, Vector


images_router = APIRouter()

EMBEDDING_TYPE_DEFAULT = "default"


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
        fields["embedding_types"] = ImageDto.get_embedding_types(image)
        return ImageDto.model_validate(fields)
    
    @staticmethod
    def get_embedding_types(image: Image):
        embedding_types = []
        if image.embedding:
            embedding_types.append(EMBEDDING_TYPE_DEFAULT)
        if image.embeddings:
            embedding_types.extend(image.embeddings.keys())
        return embedding_types


class QueryFaceClusterDto(BaseModel):
    raw_term: str
    id: str
    label: Union[str, None]


class ListImagesResult(BaseModel):
    data: List[ImageDto]
    count: int
    has_next_page: bool
    query_face_clusters: List[QueryFaceClusterDto]


@images_router.get("/api/images")
def list_images(page: int = 1, tag: Optional[str] = None, sort: Optional[Literal['asc', 'desc']] = None) -> ListImagesResult:
    limit = 20
    offset = (page - 1) * limit
    image_repo = AppGraph.get_instance(ImageRepo)
    if tag:
        tag = TagQuery.parse(tag)
        images = image_repo.list_by_tag_collected_at_desc(tag, offset, limit + 1, descending=sort != 'asc')
        count = image_repo.count_by_tag(tag)
        query_face_clusters = []
        face_cluster_repo = AppGraph.get_instance(FaceClusterRepo)
        for term in tag.terms:
            if isinstance(term.tag, TagQueryTermFace):
                fc = face_cluster_repo.get(term.tag.face_cluster_id)
                if not fc: continue
                query_face_clusters.append(QueryFaceClusterDto(
                    raw_term=str(term),
                    id=fc.id,
                    label=fc.label,
                ))
    else:
        images = image_repo.list_by_collected_at_desc(offset, limit + 1, descending=sort != 'asc')
        count = image_repo.count()
        query_face_clusters = []
    has_next_page = len(images) > limit
    images = images[:limit]
    return ListImagesResult(
        data=list(map(ImageDto.from_doc, images)),
        count=count,
        has_next_page=has_next_page,
        query_face_clusters=query_face_clusters,
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


@images_router.get("/api/images/search/similar/compare")
def search_similar_images_compare(url: str):
    with NamedTemporaryFile('wb') as f:
        with requests.get(url, stream=True) as resp:
            resp.raise_for_status()
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)
            f.flush()

        embeddings = {}

        for model_name, model_cls in (
            ("clip", ClipEmbedding),
            ("csd", CsdEmbedding),
        ):
            model = AppGraph.get_instance(model_cls)
            model.load_model()
            emb = model.extract(Path(f.name))
            embeddings[model_name] = Vector.from_numpy(emb)

        model = AppGraph.get_instance(WdAutotagger)
        model.load_model()
        emb = model.extract(Path(f.name)).embedding
        if emb is not None:
            embeddings[EMBEDDING_TYPE_DEFAULT] = Vector.from_numpy(emb)

    return _search_similar_images(embeddings)


@images_router.get("/api/images/{image_id}")
def get_image(image_id: str):
    image_repo = AppGraph.get_instance(ImageRepo)
    image = image_repo.get(image_id)
    if image is None:
        raise HTTPException(404)
    
    return ImageDto.from_doc(image)


@images_router.get("/api/images/{image_id}/similar")
def list_similar_images(image_id: str, count: int = 10, embedding_type: str = EMBEDDING_TYPE_DEFAULT):
    image_repo = AppGraph.get_instance(ImageRepo)
    image = image_repo.get(image_id)
    if image is None:
        raise HTTPException(404)
    
    if embedding_type == EMBEDDING_TYPE_DEFAULT:
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


@images_router.get("/api/images/{image_id}/similar/compare")
def list_similar_images_compare(image_id: str):
    image_repo = AppGraph.get_instance(ImageRepo)
    image = image_repo.get(image_id)
    if image is None:
        raise HTTPException(404)
    
    embeddings = dict(image.embeddings)
    if image.embedding:
        embeddings[EMBEDDING_TYPE_DEFAULT] = image.embedding
    return _search_similar_images(embeddings, image_id)


def _search_similar_images(embeddings: Dict[str, Vector], image_id: Union[str, None] = None):
    image_repo = AppGraph.get_instance(ImageRepo)

    results = []
    count = 5
    all_sim_images = {}
    if image_id:
        count += 1  # to exclude query image itself

    for embedding_type in embeddings.keys():
        index = AppGraph.get_instance(MultiEmbeddingIndexManager).get_manager(embedding_type)
        emb = embeddings[embedding_type]

        result = []
        for sim_id, score in index.search(emb.to_numpy(), count):
            if sim_id == image_id: continue
            sim_image = all_sim_images.get(sim_id) or image_repo.get(sim_id)
            if sim_image is None: continue
            all_sim_images[sim_id] = sim_image

            result.append({
                "image": ImageDto.from_doc(sim_image),
                "score": score,
            })
        
        results.append({
            "type": embedding_type,
            "images": result,
        })
    
    # extend result
    for result in results:
        embedding_type = result["type"]
        query_emb = embeddings[embedding_type]
        query_emb = query_emb.to_numpy()

        missing_image_ids = all_sim_images.keys() - set(image["image"].id for image in result["images"])
        for missing_image_id in missing_image_ids:
            missing_image = all_sim_images[missing_image_id]
            if embedding_type == EMBEDDING_TYPE_DEFAULT:
                emb = missing_image.embedding
            else:
                emb = missing_image.embeddings.get(embedding_type)
            if emb is None: continue
            emb = emb.to_numpy()

            result["images"].append({
                "image": ImageDto.from_doc(missing_image),
                "score": np.dot(query_emb, emb).astype(float) / (np.linalg.norm(query_emb) * np.linalg.norm(emb)),
            })
        
        result["images"].sort(key=lambda image: image["score"], reverse=True)
    
    return results


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
