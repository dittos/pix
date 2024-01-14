from typing_extensions import Annotated

from sqlalchemy import Engine, create_engine
from pix.config import Settings
from pix.model.base import metadata
from pix.model.image import ImageRepo
from pix.model.tweet import TweetRepo
from pixdb.db import Database
from pixdb.inject import Graph, Value


def create_graph():
    settings = Settings()
    graph = Graph(settings)

    def engine_factory(db_uri: Annotated[str, Value]):
        return create_engine(db_uri, echo=True)
    
    graph.bind_factory(Engine, engine_factory)
    
    metadata.create_all(graph.get_instance(Engine))

    return graph
