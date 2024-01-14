import datetime
from typing import List, Union
import requests
import re
import time
from urllib.parse import unquote

from bs4 import BeautifulSoup
from pix.app import create_graph

from pix.config import Settings
from pix.model.image import Image, ImageRepo
from pix.model.tweet import Attachment, Tweet, TweetRepo
from pixdb.db import Database


class Download:
    def __init__(
            self,
            settings: Settings,
            db: Database,
            tweet_repo: TweetRepo,
            image_repo: ImageRepo,
    ):
        self.settings = settings
        self.db = db
        self.tweet_repo = tweet_repo
        self.image_repo = image_repo

    def handle(self, pages: Union[int, None]):
        tweets = self._get_new_tweets(pages)
        tweets.reverse()  # to save old likes first
        attachments = self._download_images(tweets)

        with self.db.transactional():
            for tweet in tweets:
                self.tweet_repo.put(tweet.id, tweet)
            for attachment in attachments:
                image = Image(
                    local_filename=attachment.make_local_filename(),
                    collected_at=datetime.datetime.now(tz=datetime.timezone.utc),
                    source_url=attachment.url,
                    tweet_id=attachment.tweet_id,
                )
                image_id = "tw." + image.local_filename.rsplit(".", 1)[0]
                self.image_repo.put(image_id, image)

    def _get_new_tweets(self, pages: Union[int, None]):
        first_page = f"{self.settings.nitter_host}/{self.settings.twitter_username}/favorites"
        page = first_page
        result = []
        page_count = 0

        while pages is None or page_count < pages:
            if page_count > 0:
                time.sleep(self.settings.nitter_request_sleep_seconds)

            print(f"downloading from {page}")

            resp = requests.get(page)
            resp.raise_for_status()
            page_count += 1

            doc = BeautifulSoup(resp.content, features="html.parser")
            tweets = _extract_tweets(doc)
            page = first_page + doc.select(".show-more a")[-1].attrs["href"]

            found_saved = False
            for tweet in tweets:
                if pages is None and self.tweet_repo.get(tweet.id):
                    print(f"saved tweet found: {tweet.id}")
                    found_saved = True
                else:
                    result.append(tweet)
            
            if found_saved:
                break
        
        return result

    def _download_images(self, tweets: List[Tweet]) -> List[Attachment]:
        result = []
        for tweet in tweets:
            for attachment in tweet.attachments:
                download_path = self.settings.images_dir / attachment.make_local_filename()
                if download_path.exists():
                    print(f"already exists: {download_path.name}")
                else:
                    r = requests.get(attachment.url)
                    # if not r.ok:
                    #     print(f"error: {r.status_code}, {download_path.name}")
                    #     continue
                    r.raise_for_status()
                    download_path.write_bytes(r.content)
                result.append(attachment)
        return result


def _extract_tweets(doc: BeautifulSoup) -> List[Tweet]:
    result = []
    for item in doc.select(".timeline-item"):
        link_el = item.select_one(".tweet-link")
        if not link_el: continue
        tweet_id = re.search("/status/([0-9]+)", link_el.attrs["href"]).group(1)
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
        result.append(Tweet(id=tweet_id, attachments=attachments))
    return result


if __name__ == "__main__":
    # parser = argparse.ArgumentParser()
    # parser.add_argument("--pages", type=int)
    # args = parser.parse_args()

    task = create_graph().get_instance(Download)
    task.handle(1)
