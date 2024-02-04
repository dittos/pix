from pix.app import create_graph
from pix.task.download import DownloadTask
from pix.task import autotag, build_embedding_index, facedetect, facecluster


if __name__ == "__main__":
    graph = create_graph()
    graph.get_instance(DownloadTask).handle()
    graph.run(autotag.main)
    graph.run(build_embedding_index.main)
    graph.run(facedetect.main)
    graph.run(facecluster.main)
