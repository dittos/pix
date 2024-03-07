from typing import List, Union
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests

from pix.app import AppGraph
from pix.model.face_cluster import FaceClusterRepo
from pix.model.image import ImageFace, ImageRepo

face_clusters_router = APIRouter()


class FaceClusterFaceDto(BaseModel):
    image_id: str
    face: ImageFace


class FaceClusterDto(BaseModel):
    id: str
    label: Union[str, None]
    wikidata_qid: Union[str, None]
    face_count: Union[int, None]
    faces: List[FaceClusterFaceDto]


@face_clusters_router.get("/api/face-clusters")
def list_face_clusters() -> List[FaceClusterDto]:
    fc_repo = AppGraph.get_instance(FaceClusterRepo)
    image_repo = AppGraph.get_instance(ImageRepo)
    result = []
    for fc in fc_repo.all():
        face = fc.faces[0]
        result.append(FaceClusterDto(
            id=fc.id,
            label=fc.label,
            wikidata_qid=fc.wikidata_qid,
            face_count=len(fc.faces),
            faces=[FaceClusterFaceDto(
                image_id=face.image_id,
                face=image_repo.get(face.image_id).faces[face.index],
            )],
        ))
    result.sort(key=lambda fc: fc.face_count, reverse=True)
    return result


@face_clusters_router.get("/api/face-clusters/{face_cluster_id}")
def get_face_cluster(face_cluster_id: str) -> FaceClusterDto:
    fc_repo = AppGraph.get_instance(FaceClusterRepo)
    face_cluster = fc_repo.get(face_cluster_id)
    image_repo = AppGraph.get_instance(ImageRepo)
    faces = []
    for face in face_cluster.faces:
        faces.append(FaceClusterFaceDto(
            image_id=face.image_id,
            face=image_repo.get(face.image_id).faces[face.index],
        ))
    return FaceClusterDto(
        id=face_cluster.id,
        label=face_cluster.label,
        wikidata_qid=face_cluster.wikidata_qid,
        face_count=len(faces),
        faces=faces,
    )


class SetFaceClusterLabelRequest(BaseModel):
    wikidata_qid: str


@face_clusters_router.put("/api/face-clusters/{face_cluster_id}/label")
def set_face_cluster_label(face_cluster_id: str, request: SetFaceClusterLabelRequest) -> FaceClusterDto:
    fc_repo = AppGraph.get_instance(FaceClusterRepo)
    face_cluster = fc_repo.get(face_cluster_id)
    if face_cluster is None:
        raise HTTPException(404)

    r = requests.get(f"https://www.wikidata.org/entity/{request.wikidata_qid}.json")
    r.raise_for_status()
    entity = r.json()["entities"][request.wikidata_qid]
    face_cluster.wikidata_qid = request.wikidata_qid
    label = None
    for lang in "ko", "en":
        label_dict = entity["labels"].get(lang)
        if label_dict:
            label = label_dict["value"]
            break
    face_cluster.label = label
    fc_repo.update(face_cluster)

    image_repo = AppGraph.get_instance(ImageRepo)
    faces = []
    for face in face_cluster.faces:
        faces.append(FaceClusterFaceDto(
            image_id=face.image_id,
            face=image_repo.get(face.image_id).faces[face.index],
        ))
    return FaceClusterDto(
        id=face_cluster.id,
        label=face_cluster.label,
        wikidata_qid=face_cluster.wikidata_qid,
        face_count=len(faces),
        faces=faces,
    )
