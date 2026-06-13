import datetime as dt

from apify import Actor
from typing import Any, Optional

from src.RedditCrawler import RedditCrawler
from src.settings import settings
from src.core.logger import Logger
from src.util.utils import normalize_url

logger = Logger("Control")


async def push_post(actor, post, filter_fields: Optional[list[str]] = None) -> bool:
    """ pushes a post to apify only when it passes field filters """
    def _is_missing(value: Any) -> bool:
        """ check whether a field should count as missing """
        return value is None or value == "" or value == []

    filter_fields: list[str] = filter_fields or []

    if not filter_fields:
        await actor.push_items(post)
        return True

    for field in filter_fields:
        if not _is_missing(post[field]): continue
        return False

    return False


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
    max_amount: int = int(actor_input.get("maxPosts", 10) or 10)
    stop_date_raw: Optional[str] = actor_input.get("stopDate")
    filter_fields: list[str] = actor_input.get("filterFields", [])
    deep_crawl: bool = actor_input.get("deepCrawl", False)
    include_comments: bool = actor_input.get("includeComments", True)
    include_crossposts: bool = actor_input.get("includeCrossposts", True)
    cookies: list[dict[str, Any]] = actor_input.get("cookies", {})

    links: list[str] = [url for link in raw_links if (url := normalize_url(link.get("url")))]
    if proxy == {"useApifyProxy": False}:
        logger.debug("Cookies are disabled, None will be used.")
        proxy = None

    stop_date: dt.datetime = _parse_stop_date(stop_date_raw)

    loid_cookie: Optional[str] = None
    reddit_session: Optional[str] = None
    for cookie in cookies:
        name = cookie.get("name", '')
        if name == "loid": loid_cookie: str = cookie.get("value")
        elif name == "reddit_session": reddit_session: str = cookie.get("value")

    if all([loid_cookie, reddit_session]):
        settings["REDDIT_LOID_COOKIE"] = loid_cookie
        settings["REDDIT_SESSION_COOKIE"] = loid_cookie
    else:
        logger.warning("missing cookies detected, defaulting to bot's cookies (could case problems while crawling).")

    return {
        "loid_cookie": loid_cookie,
        "reddit_session": reddit_session,
        "cookies": cookies,
        "keywords": keywords,
        "links": links,
        "proxy_cfg": proxy,
        "max_amount": max_amount,
        "stop_date": stop_date,
        "filter_fields": filter_fields,
        "deep_crawl": deep_crawl,
        "include_comments": include_comments,
        "include_crossposts": include_crossposts,
    }


async def main() -> None:
    async with Actor as actor:
        actor.init()
        actor.log.debug("Actor is initialized")

        actor_inputs: dict[str, Any] = await get_actor_inputs(actor)

        settings["MAX_AMOUNT_LIMIT"] = actor_inputs["max_amount"]
        settings["STOP_DATE"] = actor_inputs["stop_date"]
        settings["DEEP_CRAWL_COMMENTS_SECTION"] = actor_inputs["deep_crawl"]
        settings["REDDIT_LOID_COOKIE"] = actor_inputs["loid_cookie"]
        settings["REDDIT_SESSION_COOKIE"] = actor_inputs["reddit_session"]
        settings["INCLUDE_COMMENTS"] = actor_inputs["include_comments"]
        settings["INCLUDE_CROSSPOSTS"] = actor_inputs["include_crossposts"]

        if not actor_inputs["links"]:
            actor.log.info('bad input - No start URLs specified in actor input, exiting...')
            await actor.exit()

        if actor_inputs["proxy_cfg"]:
            proxy_cfg = await Actor.create_proxy_configuration(actor_proxy_input=actor_inputs["proxy_cfg"])
            settings["PROXIES"] = [await proxy_cfg.new_url()]

        actor.log.info(
            f"""\n
            Actor initialized on  {settings['TODAY']}  -  with Inputs:\n
            ------------------------------------------\n            
            links:  {actor_inputs['links']}
            max_amount:  {actor_inputs['max_amount']}
            stop_date:  {actor_inputs['stop_date']}
            keywords:  {actor_inputs['keywords']}
            filter_fields:  {actor_inputs['filter_fields']}
            deep_crawl:  {actor_inputs['deep_crawl']}
            include_comments:  {actor_inputs['include_comments']}
            include_crossposts:  {actor_inputs['include_crossposts']}
            \n"""
        )

        crawler = RedditCrawler()
        actor.log.info("Crawling started - checking is done - charging user for the run")
        await actor.charge(event_name="actor-run")

        if settings["DEEP_CRAWL_COMMENTS_SECTION"]:
            valid_links: list[str] = [link for link in actor_inputs["links"] if '/comments' in link]
            await actor.charge(event_name="deep-crawl", count=len(valid_links))

        for url in actor_inputs["links"]:
            async for post in crawler.crawl(
                reddit_url=url,
                max_amount=settings["MAX_AMOUNT_LIMIT"],
                stop_date=settings["STOP_DATE"]
            ):
                if await push_post(actor, post):
                    actor.charge(event_name='pushed-result')
