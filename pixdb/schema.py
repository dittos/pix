from typing import Callable, Generic, Iterator, List, Tuple, Type, TypeVar, Union
from pydantic import BaseModel
from sqlalchemy import Column, ForeignKey, Index, MetaData, String, Table, desc

from sqlalchemy.sql.type_api import TypeEngine


T = TypeVar("T", bound=BaseModel)


class IndexField:
    def __init__(self, name: str, type: Union[Type[TypeEngine[str]], TypeEngine[str]], descending: bool = False):
        self.name = name
        self.type = type
        self.descending = descending


class Indexer(Generic[T]):
    def __init__(self, table: Table, fields: List[IndexField], entries_extractor: Callable[[T], Iterator[Tuple]]):
        self.table = table
        self.fields = fields
        self.entries_extractor = entries_extractor


def get_index_name(table_name: str, fields: List[IndexField]):
    name = f"idx_{table_name}_on_"
    for i, field in enumerate(fields):
        if i > 0:
            name += "_and_"
        name += field.name
        if field.descending:
            name += "_desc"
    return name


class Schema(Generic[T]):
    def __init__(
            self,
            doc_cls: Type[T],
            metadata: MetaData,
            table_name: Union[str, None] = None,
    ):
        self.doc_cls = doc_cls
        self.table_name = table_name or doc_cls.__name__
        self.indexers: List[Indexer] = []
        self.table = Table(
            self.table_name,
            metadata,
            Column("id", String, primary_key=True),
            Column("content", String, nullable=False),
        )

    def add_index_table(self, fields: List[IndexField], entries_extractor: Callable[[T], Iterator[Tuple]]) -> Table:
        table = Table(
            get_index_name(self.table.name, fields),
            self.table.metadata,
            *[Column(field.name, field.type) for field in fields],
            Column("id", String, ForeignKey(self.table.c.id), nullable=False),
            Index(
                None,  # generated by sqla
                *[desc(field.name) if field.descending else field.name for field in fields],
            )
        )
        self.indexers.append(Indexer(table, fields, entries_extractor))
        return table
