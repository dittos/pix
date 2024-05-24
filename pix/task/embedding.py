from pathlib import Path
from typing_extensions import Annotated
from tqdm.auto import tqdm
from pix.embeddings.clip import ClipEmbedding
from pix.model.image import ImageRepo, Vector
from pixdb.inject import Value


def main(
        image_repo: ImageRepo,
        clip_embedding: ClipEmbedding,
        images_dir: Annotated[Path, Value],
):
    clip_embedding.load_model()

    embedding_type = "clip"
    images = image_repo.list_needs_embedding(embedding_type)
    for image in tqdm(images):
        f = images_dir / image.local_filename
        embedding = clip_embedding.extract(f)
        if not image.embeddings:
            image.embeddings = {}
        if embedding_type in image.embeddings:
            continue
        image.embeddings[embedding_type] = Vector.from_numpy(embedding)
        image_repo.update(image)
