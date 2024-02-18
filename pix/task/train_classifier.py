import random
import polars as pl
from pix.model.image import ImageRepo, TagType


def main(
        image_repo: ImageRepo,
):
    examples = []
    neg_examples = []
    for image in image_repo.all():
        if image.manual_tags:
            examples.append({
                "id": image.id,
                "emb_encoded": image.embedding.data.decode(),
                "tags": [tag.tag for tag in image.manual_tags if tag.type == TagType.CHARACTER],
            })
        elif len(neg_examples) < 1000 and image.tags and any(tag.type == TagType.CHARACTER for tag in image.tags):
            neg_examples.append({
                "id": image.id,
                "emb_encoded": image.embedding.data.decode(),
                "tags": [],
            })
    
    neg_examples = random.sample(neg_examples, len(examples) * 2)
    print(f"{len(examples)=} {len(neg_examples)=}")

    df = pl.DataFrame(examples + neg_examples)
    df.write_ndjson("/home/ditto/thinkingface/data/20240211-custom-classifier-embs.json")
