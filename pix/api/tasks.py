import time
from fastapi import APIRouter

from pix.app import AppGraph
from pix.pipeline import PipelineExecutor

tasks_router = APIRouter()


@tasks_router.get("/api/tasks/pipeline/status")
def get_pipeline_status() -> dict:
    executor = AppGraph.get_instance(PipelineExecutor)
    return _get_pipeline_status(executor)


@tasks_router.post("/api/tasks/pipeline/execute")
def execute_pipeline() -> dict:
    executor = AppGraph.get_instance(PipelineExecutor)
    executor.execute()
    time.sleep(1)  # wait short time for scheduled job to start
    return _get_pipeline_status(executor)


def _get_pipeline_status(executor: PipelineExecutor) -> dict:
    return {
        "is_running": executor.is_running,
        "last_updated": executor.last_updated,
    }
