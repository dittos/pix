import datetime
from typing import List
from pydantic import BaseModel
from sqlalchemy import BigInteger, MetaData, String, create_engine, select
from pixdb.db import Database
from pixdb.doc import Doc

from pixdb.schema import IndexField, Schema
from pixdb.repo import Repo


def test_index():
    engine = create_engine("sqlite://", echo=True)
    metadata.create_all(engine)

    db = Database(engine)
    image_repo = ImageRepo(db)
    assert image_repo.get("1") is None
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    image = Image(
        created_at=now,
        tags=[ImageTag(name="red", score=0.5), ImageTag(name="big", score=0.44)]
    )
    image_repo.put("1", image)
    assert image_repo.get("1") == Doc(id="1", content=image)
    
    image2 = Image(
        created_at=now - datetime.timedelta(days=1),
        tags=[]
    )
    image_repo.put("2", image2)

    image2.tags.append(ImageTag(name="big", score=0.1))
    image_repo.put("2", image2)
    assert image_repo.get("2").content == image2

    idx_created_at = ImageRepo.idx_created_at
    r = db.execute(
        select(image_repo.table.c.id)
            .join(idx_created_at, image_repo.table.c.id == idx_created_at.c.id)
            .order_by(idx_created_at.c.created_at.desc())
    ).all()
    assert r == [("1", ), ("2", )]


metadata = MetaData()


class ImageTag(BaseModel):
    name: str
    score: float


class Image(BaseModel):
    created_at: datetime.datetime
    tags: List[ImageTag]


def datetime_to_epoch_milli(dt: datetime):
    return int(dt.timestamp() * 1000)


class ImageRepo(Repo[Image]):
    schema = Schema(Image, metadata)
    idx_created_at = schema.add_index_table(
        [IndexField("created_at", BigInteger, descending=True)],
        lambda doc: [(datetime_to_epoch_milli(doc.created_at), )],
    )
    idx_tag = schema.add_index_table(
        [IndexField("tag", String), IndexField("created_at", BigInteger, descending=True)],
        lambda doc: [(tag.name, datetime_to_epoch_milli(doc.created_at)) for tag in doc.tags],
    )
