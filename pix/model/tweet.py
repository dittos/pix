from typing import List
from pydantic import BaseModel
from pixdb.repo import Repo
from pixdb.schema import Schema

from .base import metadata


class Attachment(BaseModel):
    tweet_id: str
    type: str
    url: str

    def make_local_filename(self):
        return f"{self.tweet_id}.{self.type}.{self.url.rsplit('/', 1)[1]}"


class Tweet(BaseModel):
    id: str
    attachments: List[Attachment]


class TweetRepo(Repo[Tweet]):
    schema = Schema(Tweet, metadata)
