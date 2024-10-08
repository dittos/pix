import base64
from dataclasses import dataclass
import datetime
from enum import Enum
import numpy as np
import sqlalchemy as sa
from typing import List, Mapping, Tuple, Union
from pydantic import BaseModel
from pix.model.face_cluster import FaceClusterRepo
from pixdb.repo import Repo

from pixdb.schema import IndexField, Schema
from pix.model.base import metadata


class TagType(Enum):
    CHARACTER = "CHARACTER"
    RATING = "RATING"


class ImageTag(BaseModel):
    tag: str
    type: Union[TagType, None]
    score: Union[float, None] = None


class Vector(BaseModel):
    data: bytes
    dtype: str

    @staticmethod
    def from_numpy(arr: np.array):
        return Vector(data=base64.b64encode(arr), dtype=arr.dtype.name)
    
    def to_numpy(self) -> np.array:
        return np.frombuffer(base64.b64decode(self.data), dtype=self.dtype)


class ImageFace(BaseModel):
    x: int
    y: int
    width: int
    height: int
    embedding: Vector
    score: float
    local_filename: Union[str, None] = None


class Image(BaseModel):
    id: str
    local_filename: str
    collected_at: datetime.datetime

    source_url: Union[str, None]
    tweet_id: Union[str, None]
    tweet_username: Union[str, None] = None

    tags: Union[List[ImageTag], None] = None
    manual_tags: Union[List[ImageTag], None] = None
    embedding: Union[Vector, None] = None
    embeddings: Union[Mapping[str, Vector], None] = None
    faces: Union[List[ImageFace], None] = None

    def get_all_tags(self) -> List[ImageTag]:
        tags = []
        if self.manual_tags:
            for tag in self.manual_tags:
                tags.append(tag.model_copy(update={"score": tag.score or 1.0}))
        if self.tags:
            tags.extend(self.tags)
        return tags


@dataclass
class TagQueryTermTag:
    tag: str

    def __str__(self):
        return self.tag


@dataclass
class TagQueryTermFace:
    face_cluster_id: str

    def __str__(self):
        return "face:" + self.face_cluster_id


@dataclass
class TagQueryTerm:
    tag: Union[TagQueryTermTag, TagQueryTermFace]
    negated: bool

    def __str__(self):
        tag = str(self.tag)
        if self.negated:
            tag = "-" + tag
        return tag


@dataclass
class TagQuery:
    terms: List[TagQueryTerm]

    @staticmethod
    def parse(query: str):
        terms = []
        for expr in query.split():
            negated = False
            if expr[0] == "-":
                negated = True
                expr = expr[1:]
            if expr.startswith("face:"):
                expr = expr[len("face:"):]
                tag = TagQueryTermFace(face_cluster_id=expr)
            else:
                tag = TagQueryTermTag(expr)
            terms.append(TagQueryTerm(tag=tag, negated=negated))
        return TagQuery(terms)


class ImageRepo(Repo[Image]):
    schema = Schema(Image, metadata)
    idx_collected_at = schema.add_indexer(
        [IndexField("collected_at", sa.DateTime, descending=True)],
        lambda image: [(image.collected_at, )],
    )
    idx_tag_new = schema.add_indexer(
        [IndexField("tag", sa.String), IndexField("collected_at", sa.DateTime, descending=True)],
        lambda image: [(tag.tag, image.collected_at) for tag in image.get_all_tags()],
    )
    idx_tag_score = schema.add_indexer(
        [IndexField("tag", sa.String), IndexField("score", sa.Float, descending=True)],
        lambda image: [(tag.tag, tag.score) for tag in image.get_all_tags()],
    )
    idx_needs_autotagging = schema.add_indexer(
        [IndexField("needs_autotagging", sa.Boolean)],
        lambda image: [(True, )] if image.tags is None else [],
    )
    idx_embedding_types = schema.add_indexer(
        [IndexField("embedding_type", sa.String)],
        lambda image: [(k, ) for k in image.embeddings.keys()] if image.embeddings else [],
    )

    def count(self) -> int:
        return self.db.execute(sa.select(sa.func.count()).select_from(self.table)).first()[0]

    def list_by_collected_at_desc(self, offset: int, limit: int, descending: bool = True) -> List[Image]:
        order_by = self.idx_collected_at.c.collected_at
        if descending:
            order_by = order_by.desc()
        return [self._doc_from_row(row) for row in self.db.execute(
            sa.select(self.table)
                .join(self.idx_collected_at.table, self.table.c.id == self.idx_collected_at.c.id)
                .order_by(order_by)
                .offset(offset)
                .limit(limit)
        )]

    def list_by_tag_collected_at_desc(self, tag: TagQuery, offset: int, limit: int, descending: bool = True) -> List[Image]:
        order_by = self.idx_collected_at.c.collected_at
        if descending:
            order_by = order_by.desc()
        return [self._doc_from_row(row) for row in self.db.execute(
            sa.select(self.table)
                .join(self.idx_collected_at.table, self.idx_collected_at.c.id == self.table.c.id)
                .where(*self._tag_condition(self.table, tag))
                .order_by(order_by)
                .offset(offset)
                .limit(limit)
        )]
    
    def count_by_tag(self, tag: TagQuery) -> int:
        return self.db.execute(
            sa.select(sa.func.count())
                .select_from(self.table)
                .where(*self._tag_condition(self.table, tag))
        ).first()[0]

    def _tag_condition(self, table: sa.Table, tag: Union[str, TagQuery]):
        clauses = []
        if not isinstance(tag, TagQuery):
            tag = TagQuery.parse(tag)
        for term in tag.terms:
            if isinstance(term.tag, TagQueryTermTag):
                q = sa.select(self.idx_tag_new.c.id).where(self.idx_tag_new.c.tag == term.tag.tag)
            elif isinstance(term.tag, TagQueryTermFace):
                q = sa.select(FaceClusterRepo.idx_face_ref.c.image_id).where(FaceClusterRepo.idx_face_ref.c.id == term.tag.face_cluster_id)
            else:
                raise ValueError("unknown tag type")

            if term.negated:
                clauses.append(table.c.id.not_in(q))
            else:
                clauses.append(table.c.id.in_(q))
        return clauses
    
    def list_needs_autotagging(self) -> List[Image]:
        return [self._doc_from_row(row) for row in self.db.execute(
            sa.select(self.table)
                .join(self.idx_needs_autotagging.table, self.table.c.id == self.idx_needs_autotagging.c.id)
                .where(self.idx_needs_autotagging.c.needs_autotagging)
        )]
        
    def list_needs_embedding(self, embedding_type: str) -> List[Image]:
        return [self._doc_from_row(row) for row in self.db.execute(
            sa.select(self.table)
                .outerjoin(self.idx_embedding_types.table, (
                    (self.table.c.id == self.idx_embedding_types.c.id)
                    & (self.idx_embedding_types.c.embedding_type == embedding_type)
                ))
                .where(self.idx_embedding_types.c.embedding_type.is_(None))
        )]

    def list_has_embedding(self, embedding_type: str) -> List[Image]:
        return [self._doc_from_row(row) for row in self.db.execute(
            sa.select(self.table)
                .join(self.idx_embedding_types.table, (
                    (self.table.c.id == self.idx_embedding_types.c.id)
                    & (self.idx_embedding_types.c.embedding_type == embedding_type)
                ))
        )]
    
    def list_all_tags_with_count(self, q: Union[str, None]) -> List[Tuple[str, int]]:
        query = sa.select(self.idx_tag_score.c.tag, sa.func.count())
        if q:
            query = query.where(*self._tag_condition(self.idx_tag_score.table, q))
        return self.db.execute(
            query.group_by(self.idx_tag_score.c.tag)
        ).all()
