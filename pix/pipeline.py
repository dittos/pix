from datetime import datetime, timezone
import threading
from apscheduler.schedulers.background import BackgroundScheduler
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


class PipelineExecutor:
    def __init__(self, graph: Graph):
        self._graph = graph
        self._scheduler = BackgroundScheduler()
        self._scheduler.add_job(self._execute, trigger="cron", hour="*", minute="10")
        self.last_updated = None
        self._running = False
        self._lock = threading.Lock()
    
    def start(self):
        self._scheduler.start()
    
    def shutdown(self):
        self._scheduler.shutdown()
    
    def execute(self):
        """Manually start pipeline."""
        self._scheduler.add_job(self._execute, trigger=None)
    
    def _execute(self):
        if not self._check_and_set_running(expected=False, new_value=True):
            return
        
        try:
            run_pipeline(self._graph)
            self.last_updated = datetime.now(timezone.utc)
        finally:
            self._check_and_set_running(expected=True, new_value=False)
    
    def _check_and_set_running(self, expected: bool, new_value: bool) -> bool:
        with self._lock:
            if self._running == expected:
                self._running = new_value
                return True
            return False
    
    @property
    def is_running(self):
        with self._lock:
            return self._running


if __name__ == "__main__":
    from pix.app import create_graph
    graph = create_graph()
    run_pipeline(graph)
