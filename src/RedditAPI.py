import json.decoder
from typing import Any, Callable

from src.core.session import Session
from src.core.logger import Logger


class RedditCrawler:
    def __init__(self):
        self.normalize_url: Callable[[str], str] = lambda reddit_url: reddit_url.strip().split("?", 1)[0].replace('/.json', '').replace('//', '/') + '/.json/'

        self.session = Session()
        self.logger = Logger("RedditCrawler")

        self.logger.info("Crawler initialized successfully")

    async def fetch_json(self, reddit_url: str) -> dict[str, Any]:
        """ Fetch raw reddit json from a url """
        json_url: str = self.normalize_url(reddit_url)
        response = await self.session.get(json_url)

        try: json_response: dict[str, Any] = response.json()
        except json.decoder.JSONDecodeError as e:
            self.logger.error(f"couldn't scrape post with  e: {str(e)}  url: {reddit_url}  json_url: {json_url}")
            return {}

        self.logger.debug(f"successfully scraped json from url: {reddit_url} ")
        return json_response

    def parse_subreddit(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Parse subreddit level data from a reddit payload"""
        raise NotImplementedError

    def parse_post(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Parse post level data from a reddit payload"""
        raise NotImplementedError

    def parse_users(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        """Parse users from a reddit payload"""
        raise NotImplementedError

    def parse_comments(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        """ parse comments from a reddit payload """
        raise NotImplementedError

    def build_response(self, url: str) -> dict[str, Any]:
        """Build the final api response payload"""
        raise NotImplementedError

    async def crawl(self, reddit_url: str) -> dict[str, Any]:
        """ main function to initiate the full crawl pipeline """
        raise NotImplementedError
