from contextlib import contextmanager
from email.utils import parsedate_to_datetime
import json
from pathlib import Path
import time
from typing_extensions import Annotated
from urllib.parse import urlencode, urlparse, parse_qs
from playwright.sync_api import sync_playwright, Response

from pix.downloader.twitter_base import PaginatedResult, TwitterDownloader
from pix.model.tweet import Attachment, Tweet
from pixdb.inject import Value


def is_graphql_likes_response(response: Response):
    return 'graphql' in response.url and '/Likes?' in response.url


class TwitterPlaywrightDownloader(TwitterDownloader):
    def __init__(
            self,
            playwright_initial_cookies: Annotated[str, Value],
            playwright_storage_state_path: Annotated[Path, Value],
    ):
        self.inital_cookies = playwright_initial_cookies
        self.storage_state_path = playwright_storage_state_path
        self._page = None

    def _get_storage_state(self):
        if self.storage_state_path.exists():
            return self.storage_state_path
        
        def parse_cookie_kv(c: str):
            k, v = c.strip().split('=', 1)
            return {
                "name": k,
                "value": v,
                "domain": ".twitter.com",
                "path": "/",
                "expires": time.time() + 60*60*24*365*10,
            }

        return {
            "cookies": [parse_cookie_kv(c) for c in self.inital_cookies.split(';')]
        }
    
    @contextmanager
    def open(self):
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(storage_state=self._get_storage_state())
            self._page = page
            yield
            self._page = None
            page.context.storage_state(path=self.storage_state_path)
            browser.close()

    def get_favorites(
            self,
            username: str,
            pagination_state = None,
    ):
        page = self._page
        if pagination_state is None:
            url = f"https://twitter.com/{username}/likes"
            print(f"downloading from {url}")
            with page.expect_response(is_graphql_likes_response) as response:
                page.goto(url)
            response = response.value
            headers = response.request.headers
        else:
            url, headers = pagination_state
            print("downloading from api")
            response = page.request.get(url, headers=headers, fail_on_status_code=True)

        api_url = response.url
        body = response.json()

        next_cursor = None
        tweets = []
        for instruction in body["data"]["user"]["result"]["timeline_v2"]["timeline"]["instructions"]:
            if instruction["type"] != "TimelineAddEntries": continue
            for entry in instruction["entries"]:
                if entry["content"]["__typename"] == "TimelineTimelineCursor" and entry["content"]["cursorType"] == "Bottom":
                    next_cursor = entry["content"]["value"]

                if entry["content"]["__typename"] == "TimelineTimelineItem":
                    raw_tweet = entry["content"]["itemContent"]["tweet_results"]["result"]
                    if raw_tweet["__typename"] == "TweetWithVisibilityResults":
                        raw_tweet = raw_tweet["tweet"]

                    attachments = []
                    for media in raw_tweet["legacy"].get("extended_entities", {}).get("media", []):
                        attachments.append(Attachment(
                            tweet_id=raw_tweet["rest_id"],
                            type=media["type"],
                            url=media["media_url_https"],
                        ))
                    tweets.append(Tweet(
                        id=raw_tweet["rest_id"],
                        username=raw_tweet["core"]["user_results"]["result"]["legacy"]["screen_name"],
                        attachments=attachments,
                        raw_data=raw_tweet,
                        created_at=parsedate_to_datetime(raw_tweet["legacy"]["created_at"]),
                    ))
        
        parsed = urlparse(api_url)
        query = parse_qs(parsed.query)
        variables = json.loads(query["variables"][0])
        variables["cursor"] = next_cursor
        query["variables"] = [json.dumps(variables)]
        next_api_url = parsed._replace(query=urlencode(query, doseq=True)).geturl()
        return PaginatedResult(tweets=tweets, pagination_state=(next_api_url, headers))
