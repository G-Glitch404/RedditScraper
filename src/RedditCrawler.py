import time
import datetime as dt
import asyncio
import urllib.parse
import json.decoder

from typing import Union, Optional, Any, Coroutine, AsyncGenerator

from src.core.session import Session
from src.settings import settings
from src.core.logger import Logger
from src.items.post import Post
from src.items.comment import Comment
from src.util.utils import extract, normalize_url, pagination


class RedditCrawler:
    def __init__(self):
        self.session = Session()
        self.logger = Logger("RedditCrawler")

        self.session.headers.update({
            "Cookie": f"loid={settings['REDDIT_LOID_COOKIE']}; "
                      f"reddit_session={settings['REDDIT_SESSION_COOKIE']}",
        })

        self.comments_crawler = CommentsCrawler(self.session, self.logger)
        self.logger.info("Crawler initialized successfully")

    async def fetch_json(
            self,
            reddit_url: str,
            next_pagination: Optional[dict[str, str]] = None
    ) -> Union[list[dict[str, Any]], dict[str, Any], None]:
        """ fetch raw reddit JSON from a url """
        json_url: str = normalize_url(reddit_url)
        if next_pagination: json_url = json_url + f'?after={next_pagination["after"]}'
        response = await self.session.get(json_url)

        try: json_response: list[dict[str, Any]] = response.json()
        except json.decoder.JSONDecodeError as e:
            self.logger.error(f"couldn't scrape post with \n\n e: {str(e)} \n\n url: {reddit_url} \n\n json_url: {json_url} \n\n response_text: {response.text} \n\n response_headers: {response.headers} \n\n request_headers: {response.request.headers}\n")
            return None

        self.logger.debug(f"successfully scraped json from url: {reddit_url} ")
        return json_response

    @staticmethod
    async def _parse_subreddit(post_obj: Post, payload: dict[str, Any]) -> Post:
        """ parse subreddit level data from a reddit payload """
        post_obj["subreddit"] = extract(payload, "subreddit_name_prefixed")
        post_obj["subreddit_id"] = extract(payload, "subreddit_id")
        post_obj["total_subreddit_subs"] = extract(payload, "subreddit_subscribers")
        post_obj["subreddit_type"] = extract(payload, "subreddit_type")

        return post_obj

    @staticmethod
    async def _parse_post(post_obj: Post, payload: dict[str, Any]) -> Post:
        """ parse post level data from a reddit payload """
        post_obj["thumbnail"] = extract(payload, "media", "oembed", "thumbnail_url")
        post_obj["crosspost_parent"] = extract(payload, "crosspost_parent")
        post_obj["post_id"] = extract(payload, "name")
        post_obj["title"] = extract(payload, "title")
        post_obj["body"] = extract(payload, "selftext")
        post_obj["link"] = settings['REDDIT_ENDPOINT'] + extract(payload, "permalink")
        post_obj["total_awards"] = extract(payload, "total_awards_received")
        post_obj["is_score_hidden"] = extract(payload, "hide_score")
        post_obj["score"] = extract(payload, "score")
        post_obj["upvotes"] = extract(payload, "ups")
        post_obj["downvotes"] = extract(payload, "downs")
        post_obj["upvote_ratio"] = extract(payload, "upvote_ratio")
        post_obj["is_original_content"] = extract(payload, "is_original_content")
        post_obj["post_flair"] = extract(payload, "link_flair_text")
        post_obj["type"] = extract(payload, "post_hint", default='').split(":")[-1] or None
        post_obj["published_at"] = dt.datetime.fromtimestamp(extract(payload, "created_utc"), tz=dt.timezone.utc)
        post_obj["is_crosspostable"] = extract(payload, "is_crosspostable")
        post_obj["total_crossposts"] = extract(payload, "num_crossposts")
        post_obj["is_crosspost"] = True if post_obj["crosspost_parent"] else False
        post_obj["is_over_18"] = extract(payload, "over_18")
        post_obj["can_gild"] = extract(payload, "can_gild")
        post_obj["is_edited"] = extract(payload, "edited")
        post_obj["is_pinned"] = extract(payload, "pinned")
        post_obj["is_hidden"] = extract(payload, "hidden")
        post_obj["is_gallery"] = extract(payload, "is_gallery")
        post_obj["is_video"] = extract(payload, "is_video")
        post_obj["is_locked"] = extract(payload, "locked")
        post_obj["is_spoiler"] = extract(payload, "spoiler")
        post_obj["is_author_premium"] = extract(payload, "author_premium")

        post_obj["is_removed"] = {
            "num_reports": extract(payload, "num_reports"),
            "removed_by": extract(payload, "removed_by"),
            "reason": extract(payload, "removal_reason"),
            "is_publisher_blocked": extract(payload, "author_is_blocked"),
            "mod_reason": extract(payload, "mod_reason_by"),
        }
        post_obj["found_media"] = [
            extract(payload, 'url'),
            extract(payload, 'url_overridden_by_dest'),
            extract(payload, "preview", "reddit_video_preview", "fallback_url")
        ]

        post_obj["found_media"] = [link for link in post_obj["found_media"] if link]

        return post_obj

    @staticmethod
    async def _parse_user(post_obj: Post, payload: dict[str, Any]) -> Post:
        """ parse users from a reddit payload """
        post_obj["publisher"] = extract(payload, "author")
        post_obj["publisher_id"] = extract(payload, "author_fullname")
        post_obj["total_comments"] = extract(payload, "num_comments")
        post_obj["is_comments_still_active"] = extract(payload, "send_replies")

        return post_obj

    @staticmethod
    async def _parse_comment(raw_comment: dict[str, Any]) -> Comment:
        comment = Comment()

        comment["author"] = extract(raw_comment, "author")
        comment["author_id"] = extract(raw_comment, "author_fullname")
        comment["comment_id"] = extract(raw_comment, "name")
        comment["parent_id"] = extract(raw_comment, "parent_id")
        comment["link_id"] = extract(raw_comment, "link_id")
        comment["subreddit_id"] = extract(raw_comment, "subreddit_id")
        comment["subreddit"] = extract(raw_comment, "subreddit_name_prefixed")
        comment["body"] = extract(raw_comment, "body")
        comment["score"] = extract(raw_comment, "score")
        comment["is_score_hidden"] = extract(raw_comment, "score_hidden")
        comment["upvotes_ratio"] = extract(raw_comment, "upvotes_ratio")
        comment["downvotes"] = extract(raw_comment, "downs")
        comment["upvotes"] = extract(raw_comment, "ups")
        comment["link"] = settings['REDDIT_ENDPOINT'] + permalink if (permalink := extract(raw_comment, "permalink")) and not comment["link"] else None
        comment["can_send_replies"] = extract(raw_comment, "send_replies")
        comment["unrepliable_reason"] = extract(raw_comment, "unrepliable_reason")
        comment["is_post_comment"] = extract(raw_comment, "parent_id") == extract(raw_comment, "link_id")
        comment["is_reply"] = False if comment["is_post_comment"] else True
        comment["is_edited"] = extract(raw_comment, "edited")
        comment["is_author_blocked"] = extract(raw_comment, "author_is_blocked")
        comment["published_at"] = dt.datetime.fromtimestamp(timestamp, tz=dt.timezone.utc) if (timestamp := extract(raw_comment, "created_utc")) else None

        # Feature disabled until future updates
        # comment["replies"] = []  # storing the replies here for later, so we don't get rate limited while crawling
        # if raw_replies := extract(raw_comment, "replies", "data", "children"):
        #     comment["replies"] = (await self._parse_comment_sec(comment["link_id"], comment["subreddit"], Post(), raw_replies))['comments']

        return comment

    async def _parse_comment_sec(
            self,
            link_id: str,
            subreddit: str,
            post_obj: Post,
            payload: list[dict[str, Any]]
    ) -> Post:
        """ parse comments section from a reddit's post JSON payload """
        def append_comment(comment: Comment):
            if comment["link_id"]: post_obj["comments"].append(comment)

        async def deep_crawl(more_payload: dict[str, Any]):
            self.logger.debug(f"fetching more comments for post {link_id} - deep crawling is enabled")
            async for comment in self.comments_crawler.crawl_deep_comment_sec(subreddit, more_payload, link_id):
                append_comment(comment)

        post_obj["comments"] = []

        for raw_comment_ in payload:
            if raw_comment_["kind"] == 'more' and settings["DEEP_CRAWL_COMMENTS_SECTION"]:
                await deep_crawl(raw_comment_["data"])
            else:
                raw_comment_: dict = raw_comment_["data"]
                comment_: Comment = await self._parse_comment(raw_comment_)
                append_comment(comment_)

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
                self._parse_comment_sec(
                    link_id=payload['name'],
                    subreddit=payload['subreddit_name_prefixed'],
                    post_obj=post,
                    payload=comment_sec_payload,
                )
            )

        posts: tuple[Post, ...] = await asyncio.gather(*tasks_)
        for post in posts: post += post
        if post.insert_to_db():
            self.logger.debug(f'successfully inserted post with id: \"{post["post_id"]}\" to the database')

        return post

    async def crawl(
            self,
            reddit_url: str,
            max_amount: int = settings["MAX_AMOUNT_LIMIT"],
            stop_date: Optional[dt.datetime] = None,
    ) -> AsyncGenerator[Post, None]:
        """ main function to initiate the full crawl pipeline """
        url_path: list[str] = urllib.parse.urlparse(reddit_url).path.strip("/").split("/")
        reddit_payload: Union[dict[str, Any], list[dict[str, Any]]] = await self.fetch_json(reddit_url)
        if reddit_payload is None:
            self.logger.error(f"crawling failed for post with  link: {reddit_url}")
            return

        if "/comments/" in reddit_url:  # scraping 1 post
            start_time: float = time.time()
            self.logger.debug(f"detected a post url, initiated scraping a singler post")

            post_payload: dict[str, Any] = extract(reddit_payload, 0, "data", "children", 0, "data")
            if settings["INCLUDE_COMMENTS"]:
                comments_payload: list[dict[str, Any]] = extract(reddit_payload, 1, "data", "children")
                post: Post = await self.parse(post_payload, comments_payload)
            else:
                post: Post = await self.parse(post_payload)

            end_time: float = time.time()
            self.logger.info(f"scraped post successfully, Took: {round((end_time-start_time)/60, 2)} mins")

            yield post

        elif len(url_path) >= 2:  # scraping a subreddit/user/custom_feed (with amount limitations)
            if (not isinstance(max_amount, int)) or (max_amount > settings['MAX_AMOUNT_LIMIT']):
                self.logger.warning(f"max_amount is malformed resetting it from ({type(max_amount)}, {max_amount}) to (int, {settings['MAX_AMOUNT_LIMIT']})")
                max_amount: int = settings["MAX_AMOUNT_LIMIT"]

            self.logger.info(f"detected a large operation url, initiated scraping from a group response with   Link: {reddit_url}   max_amount: '{max_amount}'")

            extracted_posts_num: int = 0
            last_pagination: dict[str, str] = {"after": ''}
            start_time: float = time.time()

            while extracted_posts_num < max_amount:
                next_pagination: dict[str, str] = pagination(reddit_payload)
                try: stop_loop: bool = last_pagination["after"] == next_pagination["after"]
                except KeyError: stop_loop: bool = True
                if stop_loop:
                    self.logger.info('Crawler reached max found posts for this link exiting...')
                    break

                reddit_payload: Union[dict[str, Any], list[dict[str, Any]]] = await self.fetch_json(reddit_url, next_pagination)
                tasks: list[Coroutine[None, None, Post]] = [self.parse(raw_post["data"]) for raw_post in extract(reddit_payload, "data", "children")]
                extracted_posts: tuple[Post] = await asyncio.gather(*tasks)

                self.logger.debug(f"scraped {len(extracted_posts)} posts yielding results now...")
                for extracted_post in extracted_posts:
                    if isinstance(stop_date, dt.datetime) and extracted_post["published_at"] < stop_date: continue
                    if not settings["INCLUDE_CROSSPOSTS"] and extracted_post["is_crosspost"]: continue
                    yield extracted_post
                extracted_posts_num += len(extracted_posts)
                last_pagination: dict[str, str] = next_pagination

            end_time: float = time.time()
            self.logger.info(f"crawler loop exited, Found Posts: {extracted_posts_num} and Took: {round((end_time-start_time)/60, 1)} mins")

        else:
            self.logger.error(f'Possibly malformed input  url: "{reddit_url}"  max_amount: {max_amount}  crawler exiting...')
            return

        self.logger.info('Crawler finished scraping and existed successfully')


class CommentsCrawler:
    def __init__(self, session: Session, logger: Logger):
        self.session = session
        self.logger = logger

    async def _fetch_comment_sec(
            self,
            post_id: str,
            children: list[str],
    ) -> list[Union[dict[str, Any]]]:
        response = await self.session.get(url=settings["REDDIT_ENDPOINT"] + '/api/morechildren', params={
            "api_type": 'json',
            "link_id": post_id,
            "children": ','.join(children).strip(','),
            "limit_children": True,
            "raw_json": 1,
        })

        try: json_response: dict[str, Any] = response.json()
        except json.decoder.JSONDecodeError as e:
            self.logger.error(
                f"couldn't scrape post comment section  -  "
                f"\nlink: {response.request.url}\n"
                f"status_code: {response.status_code}  "
                f"e: {str(e)}  "
                f"post_id: {post_id}\n"
                f"response_text: {response.text if len(response.text) < 1700 else f'{response.text[:850]}...{response.text[-850:]}'}"
            )
            return []

        return json_response["json"]["data"]["things"]

    async def crawl_deep_comment_sec(
            self,
            subreddit: str,
            reddit_payload: dict[str, Any],
            post_id: Optional[str] = None
    ) -> AsyncGenerator[Comment, None]:
        """ crawl and collect all nested comments from comments section payload """
        post_id: str = post_id or extract(reddit_payload, 'parent_id')
        children_nodes: list[str] = extract(reddit_payload, "children")

        for idx in range(0, len(children_nodes), 99):
            node: list[str] = children_nodes[idx: idx + 99]
            comments_batch = await self._fetch_comment_sec(post_id, node)

            for raw_comment in comments_batch:
                comment = Comment()
                raw_comment: dict[str, Any] = extract(raw_comment, "data")

                comment["parent_id"] = extract(raw_comment, "parent")
                comment["link_id"] = extract(raw_comment, "link") or post_id
                comment["comment_id"] = extract(raw_comment, "id")
                comment["body"] = extract(raw_comment, "contentText")
                comment["link"] = f'{settings["REDDIT_ENDPOINT"]}/{subreddit}/comments/{post_id.split("_", 1)[-1]}/comment/{comment["comment_id"]}'

                if comment["comment_id"] and comment["link_id"]:
                    yield comment
