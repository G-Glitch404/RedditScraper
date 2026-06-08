import asyncio
import json.decoder
import time
import urllib.parse
import datetime as dt

from typing import Union, Optional, Any, Callable, Coroutine, AsyncGenerator

from src.core.session import Session
from src.items.post import Post
from src.items.comment import Comment
from src.core.logger import Logger
from src.settings import settings


class RedditCrawler:
    def __init__(self):
        self.normalize_url: Callable[[str], str] = lambda reddit_url: reddit_url.strip().split("?", 1)[0].replace('/.json', '').replace('//', '/') + '/.json'
        self.pagination: Callable[[dict], dict[str, str]] = lambda payload: {"after": payload["data"]["after"]}

        self.session = Session()
        self.logger = Logger("RedditCrawler")
        self.comments_crawler = CommentsCrawler()

        self.logger.info("Crawler initialized successfully")

    async def fetch_json(
            self,
            reddit_url: str,
            pagination: Optional[dict[str, str]] = None
    ) -> Union[list[dict[str, Any]], dict[str, Any]]:
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
    async def _parse_subreddit(post_obj: Post, payload: dict[str, Any]) -> Post:
        """ parse subreddit level data from a reddit payload """
        post_obj["subreddit"] = payload["subreddit_name_prefixed"]
        post_obj["subreddit_id"] = payload["subreddit_id"]
        post_obj["total_subreddit_subs"] = payload["subreddit_subscribers"]
        post_obj["subreddit_type"] = payload["subreddit_type"]

        return post_obj

    @staticmethod
    async def _parse_post(post_obj: Post, payload: dict[str, Any]) -> Post:
        """ parse post level data from a reddit payload """
        post_obj["thumbnail"] = payload["media"]["oembed"]["thumbnail_url"]
        post_obj["post_id"] = payload["name"]
        post_obj["title"] = payload["title"]
        post_obj["link"] = settings['REDDIT_ENDPOINT'] + payload["permalink"]
        post_obj["total_awards"] = payload["total_awards_received"]
        post_obj["is_score_hidden"] = payload["hide_score"]
        post_obj["score"] = payload["score"]
        post_obj["upvotes"] = payload["ups"]
        post_obj["downvotes"] = payload["downs"]
        post_obj["upvote_ratio"] = payload["upvote_ratio"]
        post_obj["is_original_content"] = payload["is_original_content"]
        post_obj["post_flair"] = payload["link_flair_text"]
        post_obj["type"] = payload["post_hint"].split(":")[-1]
        post_obj["published_at"] = dt.datetime.fromtimestamp(payload["created_utc"], tz=dt.timezone.utc)
        post_obj["videos_urls"] = [payload["url_overridden_by_dest"], payload["preview"]["reddit_video_preview"]["fallback_url"]]
        post_obj["is_crosspostable"] = payload["is_crosspostable"]
        post_obj["total_crossposts"] = payload["num_crossposts"]
        post_obj["is_over_18"] = payload["over_18"]
        post_obj["is_gild"] = payload["can_gild"]
        post_obj["is_edited"] = payload["edited"]
        post_obj["is_locked"] = payload["locked"]
        post_obj["is_spoiler"] = payload["spoiler"]
        post_obj["is_author_premium"] = payload["author_premium"]
        post_obj["is_removed"] = {
            "num_reports": payload["num_reports"],
            "removed_by": payload["removed_by"],
            "reason": payload["removal_reason"],
            "is_publisher_blocked": payload["author_is_blocked"],
            "mod_reason": payload["mod_reason_by"],
        }

        return post_obj

    @staticmethod
    async def _parse_user(post_obj: Post, payload: dict[str, Any]) -> Post:
        """ parse users from a reddit payload """
        post_obj["publisher"] = payload["author"]
        post_obj["publisher_id"] = payload["author_fullname"]
        post_obj["total_comments"] = payload["num_comments"]
        post_obj["is_comments_still_active"] = payload["send_replies"]

        return post_obj

    async def _parse_comment(self, raw_comment: dict[str, Any]) -> Comment:
        comment = Comment()

        comment["author"] = raw_comment["author"]
        comment["author_id"] = raw_comment["author_fullname"]
        comment["comment_id"] = raw_comment["name"]
        comment["parent_id"] = raw_comment["parent_id"]
        comment["link_id"] = raw_comment["link_id"]
        comment["subreddit_id"] = raw_comment["subreddit_id"]
        comment["subreddit"] = raw_comment["subreddit_name_prefixed"]
        comment["body"] = raw_comment["body"]
        comment["score"] = raw_comment["score"]
        comment["is_score_hidden"] = raw_comment["score_hidden"]
        comment["upvotes_ratio"] = raw_comment["upvotes_ratio"]
        comment["downvotes"] = raw_comment["downs"]
        comment["upvotes"] = raw_comment["ups"]
        comment["link"] = settings['REDDIT_ENDPOINT'] + raw_comment["permalink"]
        comment["can_send_replies"] = raw_comment["send_replies"]
        comment["unrepliable_reason"] = raw_comment["unrepliable_reason"]
        comment["is_post_comment"] = raw_comment["parent_id"] == raw_comment["link_id"]
        comment["is_reply"] = False if comment["is_post_comment"] else True
        comment["is_edited"] = comment["edited"]
        comment["is_author_blocked"] = raw_comment["author_is_blocked"]
        comment["published_at"] = dt.datetime.fromtimestamp(raw_comment["created_utc"], tz=dt.timezone.utc)
        comment["replies"] = await self.comments_crawler.crawl_comment_replies(comment["link_id"], raw_comment["replies"])

        return comment

    async def _parse_comment_sec(self, post_obj: Post, payload: list[dict[str, Any]]) -> Post:
        """ parse comments section from a reddit's post JSON payload """
        extracted_comments: int = 0
        for raw_comment_ in payload:
            if raw_comment_["kind"] == 'more':
                async for comment_ in self.comments_crawler.crawl_deep_comment_sec(raw_comment_["data"]):
                    post_obj["replies"].appened(comment_)
                    extracted_comments += 1

            raw_comment_: dict = raw_comment_["data"]
            comment_: Comment = await self._parse_comment(raw_comment_)
            post_obj["replies"].appened(comment_)
            extracted_comments += 1

        return post_obj

    async def parse(
            self,
            payload: dict[str, Any],
            comment_sec_payload: Optional[list[dict[str, Any]]] = None
    ) -> Post:
        """ async parser for different post sections """
        post = Post()
        tasks_: list[Coroutine[None, None, Post]] = [
            self._parse_post(post, payload),
            self._parse_user(post, payload),
            self._parse_subreddit(post, payload),
        ]

        if comment_sec_payload:
            tasks_.append(
                self._parse_comment_sec(post_obj=post, payload=comment_sec_payload)
            )

        posts: tuple[Post, ...] = await asyncio.gather(*tasks_)
        for post in posts: post += post
        if post.insert_to_db():
            self.logger.debug(f'successfully inserted post with id: \"{post["post_id"]}\" to the database')

        return post

    async def crawl(
            self,
            reddit_url: str,
            max_amount: int = settings["MAX_AMOUNT_LIMIT"]
    ) -> AsyncGenerator[Post, None]:
        """ main function to initiate the full crawl pipeline """
        url_path: list[str] = urllib.parse.urlparse(reddit_url).path.strip("/").split("/")
        reddit_payload: Union[dict[str, Any], list[dict[str, Any]]] = await self.fetch_json(reddit_url)

        if "/comments/" in reddit_url:  # scraping from 1 post
            self.logger.info(f"detected a post url, initiated scraping a singler post")
            post_payload: dict[str, Any] = reddit_payload[0]["data"]["children"][0]["data"]
            comments_payload: list[dict[str, Any]] = reddit_payload[1]["data"]["children"]
            yield await self.parse(post_payload, comments_payload)

        elif 2 <= len(url_path) <= 3:  # scraping a whole subreddit (with amount limitations ofc)
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
                tasks: list[Coroutine[None, None, Post]] = [self.parse(raw_post["data"]) for raw_post in reddit_payload["data"]["children"]]
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


class CommentsCrawler(RedditCrawler):
    def __init__(self):
        super(CommentsCrawler, self).__init__()

    async def _fetch_comment_sec(self, post_id: str, children: list[str]) -> list[Union[dict[str, Any], None]]:
        response = await self.session.get(
            url=settings["REDDIT_ENDPOINT"] + '/api/morechildren',
            params={
                "api_type": 'json',
                "link_id": post_id,
                "children": children,
                "limit_children": True,
                "raw_json": 1,
            },
        )

        try: json_response: dict[str, Any] = response.json()
        except json.decoder.JSONDecodeError as e:
            self.logger.error(
                f"couldn't scrape post comment section -  "
                f"e: {str(e)}  "
                f"post_id: {post_id}  "
                f"response_text: {response.text if len(response.text) < 500 else f'{response.text[:500]}...{response.text[-500:0]}'}"
            )
            return []

        return json_response["json"]["data"]["things"]

    async def crawl_deep_comment_sec(self, reddit_payload: dict[str, Any]) -> AsyncGenerator[Comment, None]:
        """ crawl and collect all nested comments from comments section payload """
        post_id: str = reddit_payload['parent_id']
        children_nodes: list[str] = reddit_payload["children"]

        for idx in range(0, len(children_nodes), 100):
            node: list[str] = children_nodes[idx: idx + 100]
            comments_batch: list[dict[str, Any]] = await self._fetch_comment_sec(post_id, node)

            for raw_comment in comments_batch:
                comment = Comment()

                comment["parent_id"] = raw_comment["parent"]
                comment["link_id"] = raw_comment["link"]
                comment["comment_id"] = raw_comment["id"]
                comment["body"] = raw_comment["contentText"]

                yield comment

    async def crawl_comment_replies(self, post_id: str, reddit_payload: dict[str, Any]) -> list[Comment]:
        """ crawl and collect all nested replies for any comment from it is payload """
        payload: dict[str, Any] = reddit_payload["data"]
        payload["parent_id"] = post_id

        return [comment async for comment in self.crawl_deep_comment_sec(payload)]
