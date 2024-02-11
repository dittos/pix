import datetime
from typing import Union
from pydantic import BaseModel
import sqlalchemy as sa

from pixdb.repo import Repo
from pixdb.schema import IndexField, Schema
from pix.model.base import metadata


class Character(BaseModel):
    id: str
    name: str
    danbooru_id: Union[int, None]
    danbooru_post_count: Union[int, None]
    danbooru_created_at: Union[datetime.datetime, None]


class CharacterRepo(Repo[Character]):
    schema = Schema(Character, metadata)
    idx_name = schema.add_index_table(
        [IndexField(name="name", type=sa.String)],
        meta_fields=[
            IndexField(name="danbooru_post_count", type=sa.Integer),
            IndexField(name="danbooru_created_at", type=sa.String),
        ],
        entries_extractor=lambda c: [(c.name, c.danbooru_post_count, c.danbooru_created_at)],
    )

    def search(self, q: str, limit: int):
        return [self._doc_from_row(row) for row in self.db.execute(
            sa.select(self.table)
                .join(self.idx_name, self.idx_name.c.id == self.table.c.id)
                .where(self.idx_name.c.name.contains(q))
                .order_by(self.idx_name.c.danbooru_post_count.desc())
                .limit(limit)
        )]
