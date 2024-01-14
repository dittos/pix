from typing import Optional
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from pix.app import create_graph
from pix.model.image import ImageRepo


app = FastAPI()
graph = create_graph()

app.mount("/static", StaticFiles(directory="pix/static"), name="static")


templates = Jinja2Templates(directory="pix/templates")


@app.get("/", response_class=HTMLResponse)
def index(request: Request, page: int = 1, tag: Optional[str] = None):
    limit = 20
    offset = (page - 1) * limit
    image_repo = graph.get_instance(ImageRepo)
    if tag:
        images = image_repo.list_by_tag_collected_at_desc(tag, offset, limit)
        count = image_repo.count_by_tag(tag)
    else:
        images = image_repo.list_by_collected_at_desc(offset, limit)
        count = image_repo.count()
    tags = sorted(image_repo.list_all_tags_with_count(), key=lambda tc: tc[1], reverse=True)
    return templates.TemplateResponse(request, "index.html", {
        "images": images,
        "count": count,
        "page": page,
        "tags": tags,
        "selected_tag": tag,
    })
