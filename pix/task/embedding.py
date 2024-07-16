from pathlib import Path
from typing_extensions import Annotated
from tqdm.auto import tqdm
from pix.embeddings.clip import ClipEmbedding
from pix.embeddings.csd import CsdEmbedding
from pix.embeddings.dinov2 import Dinov2Embedding
from pix.embeddings.resnet import ResnetEmbedding
from pix.model.image import ImageRepo, Vector
from pixdb.inject import Graph, Value


def main(
        graph: Graph,
        image_repo: ImageRepo,
        images_dir: Annotated[Path, Value],
):
    embeddings = {
        'clip': ClipEmbedding,
        'resnet': ResnetEmbedding,
        'dinov2': Dinov2Embedding,
        'csd': CsdEmbedding,
    }

    # reset_embedding = 'dinov2'
    # for image in tqdm(image_repo.list_has_embedding(reset_embedding)):
    #     if image.embeddings and reset_embedding in image.embeddings:
    #         del image.embeddings[reset_embedding]
    #         image_repo.update(image)

    for embedding_type, model_cls in embeddings.items():
        model = graph.get_instance(model_cls)
        model.load_model()

        images = image_repo.list_needs_embedding(embedding_type)
        for image in tqdm(images):
            f = images_dir / image.local_filename
            embedding = model.extract(f)
            if not image.embeddings:
                image.embeddings = {}
            if embedding_type in image.embeddings:
                continue
            image.embeddings[embedding_type] = Vector.from_numpy(embedding)
            image_repo.update(image)
