import datetime as dt

from apify import Actor
from typing import Any, Optional

from src.RedditCrawler import RedditCrawler
from src.settings import settings
from src.core.logger import Logger
from src.util.utils import normalize_url

logger = Logger("Control")

# TODO: using the filterFields in the input_schema.json filter results before pushing
# TODO: add cookies loid and reddit_session in the actor_inputs dict
# TODO: merge videos_urls and images_urls into media and filter any None
# TODO: Replies of comments are empty debug and fix


async def push_post(actor, post):
    """ push posts to apify output tables """
    pass


async def get_actor_inputs(actor) -> dict[str, Any]:
    actor_input: dict[str, Any] = await actor.get_input() or {}

    keywords: list[str] = actor_input.get('keywords', [])
    links: list[dict[str, str]] = actor_input.get('links', [])
    proxy: Optional[dict] = actor_input.get('proxyConfiguration', {"useApifyProxy": False})
    max_amount: int = actor_input.get('maxPosts', 1)
    stop_date: dt.datetime = actor_input.get('stopDate', settings["TODAY"])
    filter_fields: list[str] = actor_input.get('filterFields', [])
    deep_crawl: bool = actor_input.get('deepCrawl', False)
    loid_cookie: str = ''
    reddit_session: str = ''

    links: list[str] = [normalize_url(link['url']) for link in links]

    if proxy == {"useApifyProxy": False}:
        proxy = None

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
    }


async def main() -> None:
    async with Actor as actor:
        actor_inputs: dict[str, Any] = await get_actor_inputs(actor)

        settings["MAX_AMOUNT_LIMIT"] = actor_inputs["max_amount"]
        settings["CRAWL_COMMENTS_SECTION"] = actor_inputs["deep_crawl"]
        settings["REDDIT_LOID_COOKIE"] = actor_inputs["loid_cookie"]
        settings["REDDIT_SESSION_COOKIE"] = actor_inputs["reddit_session"]

        if not actor_inputs["links"]:
            actor.log.info('bad input - No start URLs specified in actor input, exiting...')
            await actor.exit()

        if actor_inputs["proxy_cfg"]:
            proxy_cfg = await Actor.create_proxy_configuration(actor_proxy_input=actor_inputs["proxy_cfg"])
            settings["PROXIES"] = [await proxy_cfg.new_url()]

        actor.log.info(
            f"""\n
            Actor initialized on  {settings['TODAY']}  -  with Inputs:\n
            ---------------------------------------\n            
            keywords:  {actor_inputs['keywords']}
            links:  {actor_inputs['links']}
            max_amount:  {actor_inputs['max_amount']}
            stop_date:  {actor_inputs['stop_date']}
            filter_fields:  {actor_inputs['filter_fields']}
            deep_crawl:  {actor_inputs['deep_crawl']}
            \n"""
        )

        crawler = RedditCrawler()
        actor.log.info("Crawling started - checking is done - charging user for the run")
        # TODO: Charge user here

        for url in actor_inputs["links"]:
            async for post in crawler.crawl(url):
                await push_post(actor, post)
                # TODO: Charge user here
