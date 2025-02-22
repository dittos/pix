from pathlib import Path
from typing import Union
from typing_extensions import Annotated

from tqdm.auto import tqdm
from pix.embedding_index import EmbeddingIndex
from pix.model.image import ImageRepo
from pixdb.inject import Value


def build_index(
    embedding_name: Union[str, None],
    image_repo: ImageRepo,
    embedding_index_dir: Path,
):
    index = EmbeddingIndex()

    for image in tqdm(image_repo.all(), desc=embedding_name):
        if embedding_name:
            if not image.embeddings: continue
            emb = image.embeddings.get(embedding_name)
        else:
            emb = image.embedding
        
        if not emb: continue
        emb = emb.to_numpy()
        index.add(image.id, emb)

    embedding_index_dir.mkdir(parents=True, exist_ok=True)
    index.save(embedding_index_dir)


def main(
        image_repo: ImageRepo,
        data_dir: Annotated[Path, Value],
):
    emb_dir = data_dir / "emb-index"
    build_index(None, image_repo, emb_dir / "default")
    build_index("clip", image_repo, emb_dir / "clip")
    build_index("resnet", image_repo, emb_dir / "resnet")
    build_index("dinov2", image_repo, emb_dir / "dinov2")
    build_index("csd", image_repo, emb_dir / "csd")
    build_index("siglip2", image_repo, emb_dir / "siglip2")
