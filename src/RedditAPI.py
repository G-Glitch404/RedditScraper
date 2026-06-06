import asyncio
import json.decoder
import time
import urllib.parse
from typing import Union, Optional, Any, Callable, Sequence, Coroutine, AsyncGenerator

from src.core.session import Session
from src.items.post import Post, Comment
from src.core.logger import Logger
from src.settings import settings


class RedditCrawler:
    def __init__(self):
        self.normalize_url: Callable[[str], str] = lambda reddit_url: reddit_url.strip().split("?", 1)[0].replace('/.json', '').replace('//', '/') + '/.json'
        self.pagination: Callable[[dict], dict[str, str]] = lambda payload: {"after": payload["data"]["after"]}

        self.session = Session()
        self.logger = Logger("RedditCrawler")

        self.logger.info("Crawler initialized successfully")

    async def fetch_json(self, reddit_url: str, pagination: Optional[dict[str, str]] = None) -> Union[list[dict[str, Any]], dict[str, Any]]:
        """ fetch raw reddit JSON from a url """
        json_url: str = self.normalize_url(reddit_url)
        if pagination: json_url = json_url + f'?after={pagination["after"]}'
        response = await self.session.get(json_url)

        try: json_response: list[dict[str, Any]] = response.json()
        except json.decoder.JSONDecodeError as e:
            self.logger.error(f"couldn't scrape post with  e: {str(e)}  url: {reddit_url}  json_url: {json_url}")
            return [{}]

        self.logger.debug(f"successfully scraped json from url: {reddit_url} ")
        return json_response

    @staticmethod
    async def parse_subreddit(post_obj: Post, payload: dict[str, Any]) -> Post:
        """ parse subreddit level data from a reddit payload """
        return post_obj

    @staticmethod
    async def parse_post(post_obj: Post, payload: dict[str, Any]) -> Post:
        """ parse post level data from a reddit payload """
        return post_obj

    @staticmethod
    async def parse_users(post_obj: Post, payload: dict[str, Any]) -> Post:
        """ parse users from a reddit payload """
        return post_obj

    @staticmethod
    async def parse_comments(post_obj: Post, payload: dict[str, Any]) -> Post:
        """ parse comments from a reddit payload """
        return post_obj

    async def crawl_comments_section(self, payload: dict[str, Any], reddit_url: str) -> Sequence[Comment]:
        """ crawl the whole comment section if it has more than 75 comments """
        raise NotImplementedError

    async def parse(self, reddit_url: str, payload: dict[str, Any]) -> Post:
        """ async parser for different post sections """
        post = Post()

        posts: tuple[Post, ...] = await asyncio.gather(
            self.parse_post(Post(), payload),
            self.parse_users(Post(), payload),
            self.parse_subreddit(Post(), payload),
            self.parse_comments(Post(), payload),
        )

        if settings["CRAWL_COMMENTS_SECTION"]:
            comments: Sequence[Comment] = await self.crawl_comments_section(payload, reddit_url)
            post["replies"].append(comments)

        for post in posts: post += post
        if post.insert_to_db():
            self.logger.debug(f'successfully inserted post with id: \"{post["post_id"]}\" to the database')

        return post

    async def crawl(self, reddit_url: str, max_amount: int = settings["MAX_AMOUNT_LIMIT"]) -> AsyncGenerator[Post, None]:
        """ main function to initiate the full crawl pipeline """
        url_path: list[str] = urllib.parse.urlparse(reddit_url).path.strip("/").split("/")
        reddit_payload: Union[dict[str, Any], list[dict[str, Any]]] = await self.fetch_json(reddit_url)

        if "/comments/" in reddit_url:  # scraping from 1 post
            self.logger.info(f"detected a post url, initiated scraping a singler post")
            reddit_payload: dict = reddit_payload[0]["data"]["children"][0]["data"]
            yield await self.parse(reddit_url, reddit_payload)

        elif 2 <= len(url_path) <= 3:  # scraping a whole subreddit
            if (not isinstance(max_amount, int)) or (max_amount > settings['MAX_AMOUNT_LIMIT']):
                self.logger.warning(f"max_amount is malformed resetting it from ({type(max_amount)}, {max_amount}) to (int, {settings['MAX_AMOUNT_LIMIT']})")
                max_amount: int = settings["MAX_AMOUNT_LIMIT"]

            self.logger.info(f"detected a subreddit url, initiated scraping from a subreddit with max_amount: '{max_amount}'")

            extracted_posts_num: int = 0
            last_pagination: dict[str, str] = {}
            start_time: float = time.time()

            while extracted_posts_num < max_amount:
                pagination: dict[str, str] = self.pagination(reddit_payload)
                if last_pagination["after"] == pagination["after"]:
                    self.logger.info('Crawler reached max found posts for this subreddit exiting...')
                    break

                reddit_payload: Union[dict[str, Any], list[dict[str, Any]]] = await self.fetch_json(reddit_url, pagination=pagination)
                tasks: list[Coroutine[None, None, Post]] = [self.parse(reddit_url, raw_post["data"]) for raw_post in reddit_payload["data"]["children"]]
                extracted_posts: tuple[Post] = await asyncio.gather(*tasks)

                self.logger.debug(f"scraped {len(extracted_posts)} posts yielding results now...")
                for extracted_post in extracted_posts:
                    yield extracted_post
                extracted_posts_num += len(extracted_posts)
                last_pagination: dict[str, str] = pagination

            end_time: float = time.time()
            self.logger.info(f"crawler loop exited, Found Posts: {extracted_posts_num} and Took: {round((end_time-start_time)/60, 1)} mins")

        else:
            self.logger.error(f'Possibly malformed input  url: "{reddit_url}"  max_amount: {max_amount}  crawler exiting...')
            return

        self.logger.info('Crawler finished scraping and existed successfully')
