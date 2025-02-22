from pathlib import Path
from typing_extensions import Annotated
from tqdm.auto import tqdm
from pix.embeddings.clip import ClipEmbedding
from pix.embeddings.csd import CsdEmbedding
from pix.embeddings.dinov2 import Dinov2Embedding
from pix.embeddings.resnet import ResnetEmbedding
from pix.embeddings.siglip2 import Siglip2Embedding
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
        'siglip2': Siglip2Embedding,
    }

    reset_embedding = None
    # reset_embedding = 'dinov2'
    # with image_repo.db.transactional():
    #     for image in tqdm(image_repo.list_has_embedding(reset_embedding)):
    #         if image.embeddings and reset_embedding in image.embeddings:
    #             del image.embeddings[reset_embedding]
    #             image_repo.update(image)

    for embedding_type, model_cls in embeddings.items():
        if embedding_type == reset_embedding:
            images = image_repo.all()
        else:
            images = image_repo.list_needs_embedding(embedding_type)
            if not images:
                continue

        model = graph.get_instance(model_cls)
        model.load_model()

        batch_size = getattr(model, 'batch_size', 1)

        for chunk in chunked(tqdm(images), batch_size):
            files = [images_dir / image.local_filename for image in chunk]
            if batch_size > 1:
                embeddings = model.extract_batch(files)
            else:
                embeddings = [model.extract(f) for f in files]
            
            for image, embedding in zip(chunk, embeddings):
                if not image.embeddings:
                    image.embeddings = {}
                image.embeddings[embedding_type] = Vector.from_numpy(embedding)
                image_repo.update(image)


def chunked(it, size: int):
    batch = []
    for x in it:
        batch.append(x)
        if len(batch) >= size:
            yield batch
            batch.clear()
    if batch:
        yield batch
