from typing import List
from typing_extensions import Annotated
import requests
import re
from urllib.parse import unquote

from bs4 import BeautifulSoup

from pix.downloader.twitter_base import PaginatedResult, TwitterDownloader
from pix.model.tweet import Attachment, Tweet
from pixdb.inject import Value


class TwitterNitterDownloader(TwitterDownloader):
    def __init__(
            self,
            nitter_host: Annotated[str, Value],
    ):
        self.host = nitter_host

    def get_favorites(self, username: str, pagination_state = None):
        first_page = f"{self.host}/{username}/favorites"
        page = first_page
        if pagination_state:
            page += pagination_state

        print(f"downloading from {page}")

        resp = requests.get(page)
        resp.raise_for_status()

        doc = BeautifulSoup(resp.content, features="html.parser")
        tweets = _extract_tweets(doc)
        show_more_link = doc.select(".show-more a")[-1].attrs["href"]
        
        return PaginatedResult(tweets=tweets, pagination_state=show_more_link)


def _extract_tweets(doc: BeautifulSoup) -> List[Tweet]:
    result = []
    for item in doc.select(".timeline-item"):
        link_el = item.select_one(".tweet-link")
        if not link_el: continue
        tweet_id = re.search("/status/([0-9]+)", link_el.attrs["href"]).group(1)

        username = item.select_one(".username").text.replace("@", "")

        attachments = []
        for attachment in item.select(".attachment"):
            image_link = attachment.select_one("a.still-image")
            if not image_link: continue
            type = "photo"
            url = unquote(image_link.attrs["href"].rsplit("/")[-1])
            if "twimg.com" not in url:
                url = "pbs.twimg.com/" + url
            if not url.startswith("https://"):
                url = "https://" + url
            attachments.append(Attachment(tweet_id=tweet_id, type=type, url=url))
        created_at = None  # TODO
        result.append(Tweet(id=tweet_id, username=username, attachments=attachments, created_at=created_at))
    return result
