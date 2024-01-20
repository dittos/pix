from typing_extensions import Annotated

from sqlalchemy import Engine, create_engine
from pix.config import Settings
from pix.downloader.twitter_base import TwitterDownloader
from pix.downloader.twitter_playwright import TwitterPlaywrightDownloader
from pix.model.base import metadata
from pixdb.inject import Graph, Value


def create_graph():
    settings = Settings()
    graph = Graph(settings)

    def engine_factory(db_uri: Annotated[str, Value]):
        return create_engine(db_uri, echo=True)
    
    graph.bind_factory(Engine, engine_factory)

    graph.bind_implementation(TwitterDownloader, TwitterPlaywrightDownloader)
    
    metadata.create_all(graph.get_instance(Engine))

    return graph
