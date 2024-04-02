from pathlib import Path
import random
import tempfile
from typing_extensions import Annotated
import polars as pl
from google.cloud import storage
from tqdm.auto import tqdm
from pix.model.image import Image, ImageRepo, TagType
from pixdb.inject import Value


def main(
        image_repo: ImageRepo,
        images_dir: Annotated[Path, Value],
):
    client = storage.Client()

    def upload_image(image: Image):
        uri = f"gs://ditto-personal-us-central1/pix/classifier/train/{image.local_filename}"
        blob = storage.Blob.from_string(uri, client=client)
        if not blob.exists():
            blob.upload_from_filename(images_dir / image.local_filename)
        return uri

    examples = []
    neg_examples = []
    for image in tqdm(image_repo.all()):
        if image.manual_tags:
            examples.append({
                "id": image.id,
                "image_uri": upload_image(image),
                "tags": [tag.tag for tag in image.manual_tags if tag.type == TagType.CHARACTER],
            })
        elif len(neg_examples) < 1000 and image.tags and any(tag.type == TagType.CHARACTER for tag in image.tags):
            neg_examples.append({
                "id": image.id,
                "image_uri": upload_image(image),
                "tags": [],
            })
    
    neg_examples = random.sample(neg_examples, len(examples) * 2)
    print(f"{len(examples)=} {len(neg_examples)=}")

    df = pl.DataFrame(examples + neg_examples)
    with tempfile.NamedTemporaryFile() as f:
        df.write_ndjson(f.name)
        blob = storage.Blob.from_string(f"gs://ditto-personal-us-central1/pix/classifier/train/data.ndjson", client=client)
        blob.upload_from_filename(f.name)
