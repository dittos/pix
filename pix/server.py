from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from pix.app import AppGraph, create_graph
from pix.api.tags import tags_router
from pix.api.face_clusters import face_clusters_router
from pix.api.images import images_router
from pix.api.tasks import tasks_router
from pix.config import Settings
from pix.pipeline import PipelineExecutor

graph = create_graph(debug=True)


@asynccontextmanager
async def lifespan(_: FastAPI):
    AppGraph.bind(graph)
    scheduler = graph.get_instance(PipelineExecutor)
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)
app.mount("/_images", StaticFiles(directory=graph.get_instance(Settings).images_dir), name="images")

app.include_router(tags_router)
app.include_router(images_router)
app.include_router(face_clusters_router)
app.include_router(tasks_router)
