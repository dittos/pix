from pix.app import create_graph
from pix.task.autotag import AutotagTask
from pix.task.download import DownloadTask


if __name__ == "__main__":
    graph = create_graph()
    graph.get_instance(DownloadTask).handle()
    graph.get_instance(AutotagTask).handle()
