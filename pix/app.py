from pathlib import Path
from typing import Type, TypeVar
from typing_extensions import Annotated

from sqlalchemy import Engine, create_engine
from pix.config import Settings
from pix.downloader.twitter_base import TwitterDownloader
from pix.downloader.twitter_playwright import TwitterPlaywrightDownloader
from pix.embedding_index import EmbeddingIndexManager
from pix.model.base import metadata
from pixdb.inject import Graph, Value

T = TypeVar("T")


def create_graph(debug: bool = False):
    settings = Settings()
    graph = Graph(settings)

    def engine_factory(db_uri: Annotated[str, Value]):
        return create_engine(db_uri, echo=debug)
    
    graph.bind_factory(Engine, engine_factory)

    graph.bind_implementation(TwitterDownloader, TwitterPlaywrightDownloader)

    def embedding_index_factory(data_dir: Annotated[Path, Value]):
        return EmbeddingIndexManager(data_dir / "emb-index")
    
    graph.bind_factory(EmbeddingIndexManager, embedding_index_factory)
    
    metadata.create_all(graph.get_instance(Engine))

    return graph


class AppGraph:
    @classmethod
    def bind(cls, graph: Graph):
        cls._graph = graph
    
    @classmethod
    def get_instance(cls, type: Type[T]) -> T:
        return cls._graph.get_instance(type)
