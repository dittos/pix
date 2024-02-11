from pathlib import Path
from typing_extensions import Annotated
from tqdm.auto import tqdm
from pix.autotagger.wd import WdAutotagger
from pix.model.image import ImageRepo, ImageTag, Vector
from pixdb.inject import Value


def main(
        image_repo: ImageRepo,
        autotagger: WdAutotagger,
        images_dir: Annotated[Path, Value],
):
    autotagger.load_model()

    images = image_repo.list_needs_autotagging()
    for image in tqdm(images):
        f = images_dir / image.local_filename
        result = autotagger.extract(f)
        image.tags = [ImageTag(tag=tag, type=type, score=score) for tag, type, score in result.tags]
        image.embedding = Vector.from_numpy(result.embedding)
        image_repo.update(image)
