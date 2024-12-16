from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Union
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

    def to_face_cluster_face(self):
        return FaceClusterFace(
            image_id=self.image_id,
            index=self.index,
            embedding_hash="",  # TODO
        )


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
                faces=[face.to_face_cluster_face() for face in cluster],
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
            
            primary_fcid, _ = max(face_by_existing_cluster.items(), key=lambda kv: len(kv[1]))

            if len(face_by_existing_cluster) > 1:
                try_merge_cluster(face_cluster_repo, face_by_existing_cluster)
            
            primary_fc = face_cluster_repo.get(primary_fcid)
            for face in unassigned_faces:
                primary_fc.faces.append(face.to_face_cluster_face())
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

    clt = DBSCAN(min_samples=2, eps=0.9)
    clt.fit([normalize(face.embedding) for face in faces])

    clustered_faces = defaultdict(list)

    for face, label in zip(faces, clt.labels_):
        if label == -1: continue
        clustered_faces[label].append(face)
    
    return list(clustered_faces.values())


def try_merge_cluster(
    face_cluster_repo: FaceClusterRepo,
    face_by_existing_cluster: Dict[str, List[Face]],
):
    primary_fcid, _ = max(face_by_existing_cluster.items(), key=lambda kv: len(kv[1]))

    for face_cluster_id, faces in face_by_existing_cluster.items():
        print(f"{face_cluster_id}: {len(faces)} faces")
    if input(f"Confirm merge into {primary_fcid} (y/n): ") != "y":
        raise Exception("collision")
    
    with face_cluster_repo.db.transactional():
        primary_fc = face_cluster_repo.get(primary_fcid)
        other_face_clusters = [
            face_cluster_repo.get(fcid)
            for fcid in face_by_existing_cluster.keys()
            if fcid != primary_fcid
        ]
        for fc in other_face_clusters:
            if len(fc.faces) != len(face_by_existing_cluster[fc.id]):
                raise Exception("cluster split")
            primary_fc.faces.extend([
                face.to_face_cluster_face()
                for face in face_by_existing_cluster[fc.id]
            ])

            # TODO: actually delete rows
            fc.faces = []
            face_cluster_repo.update(fc)
        face_cluster_repo.update(primary_fc)
