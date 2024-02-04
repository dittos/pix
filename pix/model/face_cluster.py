import sqlalchemy as sa
from typing import List, Union
from pydantic import BaseModel
from pixdb.doc import Doc
from pixdb.repo import Repo

from pixdb.schema import IndexField, Schema
from pix.model.base import metadata


class FaceClusterFace(BaseModel):
    image_id: str
    index: int
    embedding_hash: str


class FaceCluster(BaseModel):
    label: Union[str, None]
    wikidata_qid: Union[str, None] = None
    faces: List[FaceClusterFace]


class FaceClusterRepo(Repo[FaceCluster]):
    schema = Schema(FaceCluster, metadata)
    idx_face_ref = schema.add_index_table(
        [IndexField("image_id", sa.String), IndexField("index", sa.Integer)],
        lambda fc: [(face.image_id, face.index) for face in fc.faces]
    )

    def get_by_face_ref(self, image_id: str, index: int) -> Union[Doc[FaceCluster], None]:
        fc = self.db.execute(
            sa.select(self.table)
                .join(self.idx_face_ref, self.idx_face_ref.c.id == self.table.c.id)
                .where((self.idx_face_ref.c.image_id == image_id) & (self.idx_face_ref.c.index == index))
        ).first()
        if fc is None:
            return None
        return self._doc_from_row(fc)
