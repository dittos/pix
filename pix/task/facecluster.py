from collections import defaultdict
import uuid
import numpy as np
from sklearn.cluster import DBSCAN

from pix.model.face_cluster import FaceCluster, FaceClusterFace, FaceClusterRepo
from pix.model.image import ImageRepo


def main(
    image_repo: ImageRepo,
    face_cluster_repo: FaceClusterRepo,
):
    refs = []
    fcids = []
    embs = []
    for image in image_repo.all():
        if not image.faces: continue
        for i, face in enumerate(image.faces):
            refs.append((image.id, i))
            fc = face_cluster_repo.get_by_face_ref(image.id, i)
            if fc:
                fcids.append(fc.id)
            else:
                fcids.append(None)
            embs.append(face.embedding.to_numpy())

    def normalize(v):
        return v / np.linalg.norm(v)

    clt = DBSCAN(min_samples=2, eps=0.95)
    clt.fit(list(map(normalize, embs)))

    faces = defaultdict(list)

    for ref, fcid, label in zip(refs, fcids, clt.labels_):
        if label == -1: continue
        faces[label].append((ref, fcid))
    
    for fc in faces.values():
        if all(fcid is None for _, fcid in fc):
            fcid = uuid.uuid4().hex
            face_cluster_repo.update(FaceCluster(
                id=fcid,
                label=None,
                faces=[
                    FaceClusterFace(
                        image_id=ref[0],
                        index=ref[1],
                        embedding_hash="",  # TODO
                    ) for ref, _ in fc
                ],
            ))
        else:
            primary_fcid = None
            for ref, fcid in fc:
                if not fcid: continue
                if primary_fcid is not None and primary_fcid != fcid:
                    raise ValueError("collision")
                primary_fcid = fcid
            
            assert primary_fcid
            primary_fc = face_cluster_repo.get(primary_fcid)
            for ref, fcid in fc:
                if fcid: continue
                primary_fc.faces.append(
                    FaceClusterFace(
                        image_id=ref[0],
                        index=ref[1],
                        embedding_hash="",  # TODO
                    )
                )
            face_cluster_repo.update(primary_fc)
