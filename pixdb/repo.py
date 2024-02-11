import json
from typing import ClassVar, Generic, Iterator, TypeVar, Union

from pydantic import BaseModel
from sqlalchemy import Row, select, insert, update, delete
from pixdb.db import Database

from pixdb.schema import Schema
from pixdb.db import Database


T = TypeVar("T", bound=BaseModel)


class Repo(Generic[T]):
    schema: ClassVar[Schema[T]]

    def __init__(self, db: Database):
        self.table = self.schema.table
        self.db = db
    
    def get(self, id: str) -> Union[T, None]:
        row = self.db.execute(select(self.table).where(self.table.c.id == id)).first()
        return self._doc_from_row(row)
    
    def put(self, id: str, doc: T):
        content = doc.model_dump_json(exclude={"id"})

        with self.db.transactional():
            existing = self.db.execute(select(self.table.c.id).where(self.table.c.id == id).with_for_update()).first()
            if existing:
                self.db.execute(update(self.table).values(content=content).where(self.table.c.id == id))
            else:
                self.db.execute(insert(self.table).values(id=id, content=content))

            for indexer in self.schema.indexers:
                index_table = indexer.table
                self.db.execute(delete(index_table).where(index_table.c.id == id))
                entries = [entry + (id, ) for entry in indexer.entries_extractor(doc)]
                if entries:
                    self.db.execute(insert(index_table).values(entries))
    
    def update(self, doc: T):
        # TODO: optimistic locking
        self.put(doc.id, doc)

    def all(self) -> Iterator[T]:
        return (self._doc_from_row(row) for row in self.db.execute(select(self.table)))
    
    def _doc_from_row(self, row: Union[Row, None]) -> Union[T, None]:
        if row is None:
            return None
        content = json.loads(row.content)
        content["id"] = row.id
        return self.schema.doc_cls.model_validate(content)
