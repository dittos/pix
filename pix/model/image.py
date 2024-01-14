import datetime
import sqlalchemy as sa
from typing import List, Tuple, Union
from pydantic import BaseModel
from pixdb.doc import Doc
from pixdb.repo import Repo

from pixdb.schema import IndexField, Schema
from pix.model.base import metadata


class ImageTag(BaseModel):
    tag: str
    score: Union[float, None]


class Image(BaseModel):
    local_filename: str
    collected_at: datetime.datetime

    source_url: Union[str, None]
    tweet_id: Union[str, None]

    tags: Union[List[ImageTag], None] = None


class ImageRepo(Repo[Image]):
    schema = Schema(Image, metadata)
    idx_collected_at = schema.add_index_table(
        [IndexField("collected_at", sa.DateTime, descending=True)],
        lambda image: [(image.collected_at, )],
    )
    idx_tag_new = schema.add_index_table(
        [IndexField("tag", sa.String), IndexField("collected_at", sa.DateTime, descending=True)],
        lambda image: [(tag.tag, image.collected_at) for tag in image.tags] if image.tags else [],
    )
    idx_tag_score = schema.add_index_table(
        [IndexField("tag", sa.String), IndexField("score", sa.Float, descending=True)],
        lambda image: [(tag.tag, tag.score) for tag in image.tags] if image.tags else [],
    )
    idx_needs_autotagging = schema.add_index_table(
        [IndexField("needs_autotagging", sa.Boolean)],
        lambda image: [(image.tags is None, )],
    )

    def count(self) -> int:
        return self.db.execute(sa.select(sa.func.count()).select_from(self.table)).first()[0]

    def list_by_collected_at_desc(self, offset: int, limit: int) -> List[Doc[Image]]:
        return [self._doc_from_row(row) for row in self.db.execute(
            sa.select(self.table)
                .join(self.idx_collected_at, self.table.c.id == self.idx_collected_at.c.id)
                .order_by(self.idx_collected_at.c.collected_at.desc())
                .offset(offset)
                .limit(limit)
        )]

    def list_by_tag_collected_at_desc(self, tag: str, offset: int, limit: int) -> List[Doc[Image]]:
        return [self._doc_from_row(row) for row in self.db.execute(
            sa.select(self.table)
                .join(self.idx_tag_new, self.table.c.id == self.idx_tag_new.c.id)
                .where(self.idx_tag_new.c.tag == tag)
                .order_by(self.idx_tag_new.c.collected_at.desc())
                .offset(offset)
                .limit(limit)
        )]
    
    def count_by_tag(self, tag: str) -> List[Doc[Image]]:
        return self.db.execute(
            sa.select(sa.func.count())
                .select_from(self.idx_tag_new)
                .where(self.idx_tag_new.c.tag == tag)
        ).first()[0]
    
    def list_needs_autotagging(self) -> List[Doc[Image]]:
        return [self._doc_from_row(row) for row in self.db.execute(
            sa.select(self.table)
                .join(self.idx_needs_autotagging, self.table.c.id == self.idx_needs_autotagging.c.id)
                .where(self.idx_needs_autotagging.c.needs_autotagging)
        )]
    
    def list_all_tags_with_count(self) -> List[Tuple[str, int]]:
        return self.db.execute(
            sa.select(self.idx_tag_score.c.tag, sa.func.count())
                .group_by(self.idx_tag_score.c.tag)
        ).all()
