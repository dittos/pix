from pathlib import Path
from typing_extensions import Annotated
from tqdm.auto import tqdm
from pix.autotagger.wd import WdAutotagger
from pix.model.image import ImageRepo, ImageTag, Vector
from pixdb.inject import Value


def autotag(
        image_repo: ImageRepo,
        autotagger: WdAutotagger,
        images_dir: Annotated[Path, Value],
):
    autotagger.load_model()

    images = image_repo.list_needs_autotagging()
    for image in tqdm(images):
        f = images_dir / image.content.local_filename
        result = autotagger.extract(f)
        image.content.tags = [ImageTag(tag=tag, type=type, score=score) for tag, type, score in result.tags]
        image.content.embedding = Vector.from_numpy(result.embedding)
        image_repo.put(image.id, image.content)
