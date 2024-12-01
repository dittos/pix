from collections import defaultdict
from dataclasses import dataclass
from typing import List, Union
import uuid
import numpy as np
from sklearn.cluster import DBSCAN

from pix.model.face_cluster import FaceCluster, FaceClusterFace, FaceClusterRepo
from pix.model.image import ImageRepo


@dataclass
class Face:
    image_id: str
    index: int
    face_cluster_id: Union[str, None]
    embedding: np.array


def main(
    image_repo: ImageRepo,
    face_cluster_repo: FaceClusterRepo,
):
    faces = get_all_faces(image_repo, face_cluster_repo)

    for cluster in cluster_faces(faces):
        if all(face.face_cluster_id is None for face in cluster):
            # new cluster
            fcid = uuid.uuid4().hex
            face_cluster_repo.update(FaceCluster(
                id=fcid,
                label=None,
                faces=[
                    FaceClusterFace(
                        image_id=face.image_id,
                        index=face.index,
                        embedding_hash="",  # TODO
                    ) for face in cluster
                ],
            ))
        else:
            # existing cluster

            face_by_existing_cluster = defaultdict(list)
            unassigned_faces = []
            for face in cluster:
                if face.face_cluster_id:
                    face_by_existing_cluster[face.face_cluster_id].append(face)
                else:
                    unassigned_faces.append(face)
            
            if len(face_by_existing_cluster) > 1:
                raise Exception("collision")
            
            primary_fcid = next(iter(face_by_existing_cluster.keys()))
            primary_fc = face_cluster_repo.get(primary_fcid)
            for face in unassigned_faces:
                primary_fc.faces.append(
                    FaceClusterFace(
                        image_id=face.image_id,
                        index=face.index,
                        embedding_hash="",  # TODO
                    )
                )
            face_cluster_repo.update(primary_fc)


def get_all_faces(
    image_repo: ImageRepo,
    face_cluster_repo: FaceClusterRepo,
):
    faces = []
    for image in image_repo.all():
        if not image.faces: continue
        for i, image_face in enumerate(image.faces):
            face = Face(
                image_id=image.id,
                index=i,
                face_cluster_id=None,
                embedding=image_face.embedding.to_numpy(),
            )
            fc = face_cluster_repo.get_by_face_ref(image.id, i)
            if fc:
                face.face_cluster_id = fc.id
            faces.append(face)
    return faces


def cluster_faces(faces: List[Face]) -> List[List[Face]]:
    def normalize(v):
        return v / np.linalg.norm(v)

    clt = DBSCAN(min_samples=2, eps=0.95)
    clt.fit([normalize(face.embedding) for face in faces])

    clustered_faces = defaultdict(list)

    for face, label in zip(faces, clt.labels_):
        if label == -1: continue
        clustered_faces[label].append(face)
    
    return list(clustered_faces.values())
