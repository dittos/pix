from pix.app import create_graph
from pix.task.autotag import autotag
from pix.task.build_embedding_index import build_embedding_index
from pix.task.download import DownloadTask


if __name__ == "__main__":
    graph = create_graph()
    graph.get_instance(DownloadTask).handle()
    graph.run(autotag)
    graph.run(build_embedding_index)
