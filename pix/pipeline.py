from pix.task.download import DownloadTask
from pix.task import autotag, embedding, build_embedding_index, facedetect, facecluster
from pixdb.inject import Graph


def run_pipeline(graph: Graph):
    graph.get_instance(DownloadTask).handle()
    graph.run(autotag.main)
    graph.run(embedding.main)
    graph.run(build_embedding_index.main)
    graph.run(facedetect.main)
    graph.run(facecluster.main)


if __name__ == "__main__":
    from pix.app import create_graph
    graph = create_graph()
    run_pipeline(graph)
