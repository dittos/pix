import datetime
from typing import List, Mapping, Union
from sqlalchemy import create_engine
from pix.model.base import metadata
from pix.model.image import Image, ImageRepo, ImageTag, Vector
from pixdb.db import Database


def test_list_by_tag_collected_at_desc():
    engine = create_engine("sqlite://", echo=True)
    db = Database(engine)
    metadata.create_all(engine)
    image_repo = ImageRepo(db)

    image_repo.update(_new_image("a", tags=["a"]))
    image_repo.update(_new_image("ab", tags=["a", "b"]))

    assert set(doc.id for doc in image_repo.list_by_tag_collected_at_desc("a", 0, 10)) == {"a", "ab"}
    assert set(doc.id for doc in image_repo.list_by_tag_collected_at_desc("a b", 0, 10)) == {"ab"}
    assert set(doc.id for doc in image_repo.list_by_tag_collected_at_desc("a -b", 0, 10)) == {"a"}
    assert set(doc.id for doc in image_repo.list_by_tag_collected_at_desc("-b", 0, 10)) == {"a"}


def test_list_needs_embedding():
    engine = create_engine("sqlite://", echo=True)
    db = Database(engine)
    metadata.create_all(engine)
    image_repo = ImageRepo(db)

    image_repo.update(_new_image("empty", embeddings={}))
    image_repo.update(_new_image("no_clip", embeddings={"resnet": Vector(data=b"", dtype="float32")}))
    image_repo.update(_new_image("clip", embeddings={"clip": Vector(data=b"", dtype="float32")}))

    assert set(doc.id for doc in image_repo.list_needs_embedding("clip")) == {"empty", "no_clip"}


def _new_image(id: str, *, tags: Union[List[str], None] = None, embeddings: Union[Mapping[str, Vector], None] = None):
    return Image(
        id=id,
        local_filename="",
        collected_at=datetime.datetime.now(),

        source_url=None,
        tweet_id=None,
        tweet_username=None,

        tags=[ImageTag(tag=tag, score=None, type=None) for tag in tags or []],
        embeddings=embeddings,
    )
