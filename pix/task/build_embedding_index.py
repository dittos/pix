from pathlib import Path
from typing_extensions import Annotated

from tqdm.auto import tqdm
from pix.embedding_index import EmbeddingIndex
from pix.model.image import ImageRepo
from pixdb.inject import Value


def main(
        image_repo: ImageRepo,
        data_dir: Annotated[Path, Value],
):
    index = EmbeddingIndex()

    for image in tqdm(image_repo.all()):
        if not image.content.embedding: continue
        emb = image.content.embedding.to_numpy()
        index.add(image.id, emb)

    embedding_index_dir = data_dir / "emb-index"
    embedding_index_dir.mkdir(parents=True, exist_ok=True)
    index.save(embedding_index_dir)
