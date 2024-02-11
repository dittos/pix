import datetime
import time
from typing import List, Tuple, Union
import requests

from pix.config import Settings
from pix.downloader.twitter_base import TwitterDownloader
from pix.model.image import Image, ImageRepo
from pix.model.tweet import Attachment, Tweet, TweetRepo
from pixdb.db import Database


class DownloadTask:
    def __init__(
            self,
            settings: Settings,
            db: Database,
            tweet_repo: TweetRepo,
            image_repo: ImageRepo,
            twitter_downloader: TwitterDownloader,
    ):
        self.settings = settings
        self.db = db
        self.tweet_repo = tweet_repo
        self.image_repo = image_repo
        self.twitter_downloader = twitter_downloader

    def handle(self, pages: Union[int, None] = None):
        tweets = self._get_new_tweets(pages)
        tweets.reverse()  # to save old likes first
        attachments = self._download_images(tweets)

        with self.db.transactional():
            for tweet in tweets:
                self.tweet_repo.put(tweet.id, tweet)
            
            for tweet, attachment in attachments:
                collected_at = datetime.datetime.now(tz=datetime.timezone.utc)
                if pages is not None and tweet.created_at:
                    collected_at = tweet.created_at
                
                image_id = "tw." + image.local_filename.rsplit(".", 1)[0]
                image = Image(
                    id=image_id,
                    local_filename=attachment.make_local_filename(),
                    collected_at=collected_at,
                    source_url=attachment.url,
                    tweet_id=tweet.id,
                    tweet_username=tweet.username,
                )
                self.image_repo.update(image)

    def _get_new_tweets(self, pages: Union[int, None] = None):
        with self.twitter_downloader.open():
            page_count = 0
            tweets = []
            pagination_state = None

            while pages is None or page_count < pages:
                if page_count >= 1:
                    time.sleep(self.settings.twitter_request_sleep_seconds)

                result = self.twitter_downloader.get_favorites(username=self.settings.twitter_username, pagination_state=pagination_state)
                page_count += 1
                pagination_state = result.pagination_state

                found_saved = False
                for tweet in result.tweets:
                    if self.tweet_repo.get(tweet.id):
                        print(f"saved tweet found: {tweet.id}")
                        found_saved = True
                    else:
                        tweets.append(tweet)
                
                if found_saved and pages is None:
                    break
            
            return tweets

    def _download_images(self, tweets: List[Tweet]) -> List[Tuple[Tweet, Attachment]]:
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
                result.append((tweet, attachment))
        return result
