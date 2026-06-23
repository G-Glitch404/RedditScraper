import datetime as dt

from apify import Actor
from typing import Any, Optional

from src.RedditCrawler import RedditCrawler
from src.settings import settings
from src.core.logger import Logger
from src.items.post import Post
from src.util.utils import normalize_url

logger = Logger("Control")


async def charge_user(actor, event_name: str) -> None:
    """ charge the user for an event """
    charge_event = await actor.charge(event_name=event_name)
    if charge_event.event_charge_limit_reached:
        logger.warning(f"charge event '{event_name}' limit reached, exiting...")
        await actor.exit()


async def push_post(
    actor,
    post: Post,
    filter_fields: Optional[list[str]] = None,
    keywords: Optional[list[str]] = None,
    include_removed_comments: bool = False,
    include_removed_posts: bool = False,
) -> bool:
    """push a post to apify only when it passes field and keyword filters"""
    def _is_missing(value: Any) -> bool:
        return value is None or value == "" or value == [] or value == {} or value == ()

    def _collect_text(value: Any) -> str:
        if value is None: return ""
        if isinstance(value, str): return value
        if isinstance(value, dict): return " ".join(_collect_text(v) for v in value.values())
        if isinstance(value, (list, tuple, set)): return " ".join(_collect_text(v) for v in value)

        return str(value)

    post_dict: dict[str, Any] = post.as_dict()
    filter_fields = filter_fields or []
    keywords = [k.strip().lower() for k in (keywords or []) if k and k.strip()]

    if filter_fields:
        for field in filter_fields:
            if _is_missing(post_dict.get(field)):
                return False

    if keywords:
        searchable_text = _collect_text(
            {
                "title": post_dict.get("title"),
                "body": post_dict.get("body"),
                "post_flair": post_dict.get("post_flair"),
                "publisher": post_dict.get("publisher"),
                "subreddit": post_dict.get("subreddit"),
                "comments": post_dict.get("comments"),
                "found_media": post_dict.get("found_media"),
            }
        ).lower()

        if not any(keyword in searchable_text for keyword in keywords):
            return False

    if not include_removed_comments and post_dict["comments"]:
        post_dict["comments"] = [comment for comment in post_dict.get("comments", []) if not comment.get("is_removed")]

    if not include_removed_posts and post_dict.get("is_removed"):
        return False

    await actor.push_data(post_dict)
    return True


async def get_actor_inputs(actor) -> dict[str, Any]:
    """ extract and normalize apify actor inputs """
    def _parse_stop_date(value: Optional[str]) -> Optional[dt.datetime]:
        """ parse the actor stop date into utc datetime """
        if not value: return None
        parsed = dt.datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.timezone.utc)
        return parsed.astimezone(dt.timezone.utc)

    actor_input: dict[str, Any] = await actor.get_input() or {}

    keywords: list[str] = actor_input.get("keywords", [])
    raw_links: list[dict[str, str]] = actor_input.get("links", []) or []
    proxy: Optional[dict[str, Any]] = actor_input.get("proxyConfiguration", {"useApifyProxy": False})
    max_amount: int = int(actor_input.get("maxPosts", 1000) or 10)
    stop_date_raw: Optional[str] = actor_input.get("stopDate")
    filter_fields: list[str] = actor_input.get("filterFields", [])
    deep_crawl: bool = actor_input.get("deepCrawl", False)
    include_comments: bool = actor_input.get("includeComments", True)
    include_crossposts: bool = actor_input.get("includeCrossposts", True)
    include_removed_comments: bool = actor_input.get("includeRemovedComments", False)
    include_removed_posts: bool = actor_input.get("includeRemovedPosts", False)
    cookies: dict[str, Any] = actor_input.get("cookies", {}) or {}

    links: list[str] = [url for link in raw_links if (url := normalize_url(link.get("url")))]
    if proxy == {"useApifyProxy": False}:
        logger.debug("Proxies are disabled, None will be used.")
        proxy = None

    stop_date: dt.datetime = _parse_stop_date(stop_date_raw)

    loid_cookie: Optional[str] = None
    reddit_session: Optional[str] = None
    for cookie_k, cookie_v in cookies.items():
        cookie_k = str(cookie_k).lower()
        if cookie_k == "loid": loid_cookie: str = cookie_v
        elif cookie_k == "reddit_session": reddit_session: str = cookie_v

    if all([loid_cookie, reddit_session]):
        settings["REDDIT_LOID_COOKIE"] = loid_cookie
        settings["REDDIT_SESSION_COOKIE"] = reddit_session
    else:
        logger.warning("missing cookies detected, defaulting to bot's cookies (could case problems while crawling).")

    return {
        "loid_cookie": loid_cookie,
        "reddit_session": reddit_session,
        "keywords": keywords,
        "links": links,
        "proxy_cfg": proxy,
        "max_amount": max_amount,
        "stop_date": stop_date,
        "filter_fields": filter_fields,
        "deep_crawl": deep_crawl,
        "include_comments": include_comments,
        "include_removed_comments": include_removed_comments,
        "include_removed_posts": include_removed_posts,
        "include_crossposts": include_crossposts,
    }


async def main() -> None:
    async with Actor as actor:
        actor.log.debug("Actor is initialized")

        actor_inputs: dict[str, Any] = await get_actor_inputs(actor)

        settings["MAX_AMOUNT_LIMIT"] = actor_inputs["max_amount"]
        settings["STOP_DATE"] = actor_inputs["stop_date"]
        settings["INCLUDE_COMMENTS"] = actor_inputs["include_comments"]
        settings["INCLUDE_CROSSPOSTS"] = actor_inputs["include_crossposts"]

        if all([actor_inputs["loid_cookie"], actor_inputs["reddit_session"]]):
            settings["DEEP_CRAWL_COMMENTS_SECTION"] = actor_inputs["deep_crawl"]
            logger.info("Deep crawl for comments enabled with provided cookies, extra charges will be applied.")
        elif actor_inputs["deep_crawl"]:
            logger.warning("Deep crawl for comments requires cookies to be provided, deep crawl will be disabled and crawler will return normal data without an extra charge")
            settings["DEEP_CRAWL_COMMENTS_SECTION"] = False

        if not actor_inputs["links"]:
            actor.log.info('bad input - No start URLs specified in actor input, exiting...')
            await actor.exit()

        if actor_inputs["proxy_cfg"]:
            proxy_cfg = await Actor.create_proxy_configuration(actor_proxy_input=actor_inputs["proxy_cfg"])
            settings["PROXIES"] = [await proxy_cfg.new_url()]

        actor.log.info(
            f"""\n
            Actor initialized on  {dt.datetime.now(dt.timezone.utc).isoformat()}  -  with Inputs:\n
            ------------------------------------------\n            
            links:  {actor_inputs['links']}
            max_amount:  {actor_inputs['max_amount']}
            stop_date:  {actor_inputs['stop_date']}
            keywords:  {actor_inputs['keywords']}
            filter_fields:  {actor_inputs['filter_fields']}
            deep_crawl:  {actor_inputs['deep_crawl']}
            include_comments:  {actor_inputs['include_comments']}
            include_removed_comments:  {actor_inputs['include_removed_comments']}
            include_removed_posts:  {actor_inputs['include_removed_posts']}
            include_crossposts:  {actor_inputs['include_crossposts']}
            \n"""
        )

        crawler = RedditCrawler()
        actor.log.info("Crawling started - checking is done - charging user for the run")
        await charge_user(actor, event_name='actor-run')

        if settings["DEEP_CRAWL_COMMENTS_SECTION"]:
            valid_links: list[str] = [link for link in actor_inputs["links"] if '/comments' in link]
            logger.info(f'charged user for a deep crawl of {len(valid_links)} posts')
            await charge_user(actor, event_name='deep-crawl')

        valid_posts: int = 1
        for url in actor_inputs["links"]:
            async for post in crawler.crawl(
                reddit_url=url,
                max_amount=settings["MAX_AMOUNT_LIMIT"],
                stop_date=settings["STOP_DATE"]
            ):
                post["published_at"] = str(post["published_at"])
                if await push_post(
                    actor,
                    post,
                    filter_fields=actor_inputs["filter_fields"],
                    keywords=actor_inputs["keywords"]
                ):
                    valid_posts += 1
                    await charge_user(actor, event_name='pushed-result')

        logger.info(f"actor pushed & charged user for {valid_posts} valid posts, now actor is finished and exiting...")

