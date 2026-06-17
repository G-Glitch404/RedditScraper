import asyncio
import datetime as dt

from typing import Union, Optional, Any
from urllib.parse import urlparse, urlunparse

from flask import Flask, jsonify, request

from src.RedditCrawler import RedditCrawler
from src.settings import settings
from src.core.logger import Logger

logger = Logger("CrawlerAPI")
app = Flask(__name__)

app.config["JSON_SORT_KEYS"] = False
ALLOWED_NETLOCS: set[str] = {
    "reddit.com",
    "www.reddit.com",
    "old.reddit.com",
    "m.reddit.com",
    "new.reddit.com",
    "redd.it",
}


def normalize_reddit_json_url(url: str) -> Union[str, bool]:
    """ ensures the input links are reddit.com links """
    parsed = urlparse(url.strip())

    netloc: str = parsed.netloc.lower()
    if not parsed.scheme or not parsed.netloc or netloc not in ALLOWED_NETLOCS:
        logger.error(f'malformed or bad input  -  url:  "{url}"')
        return False

    path = parsed.path or "/"
    if path.endswith(".json"): normalized_path = path
    else: normalized_path = path.rstrip("/") + "/.json"

    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            normalized_path,
            parsed.params,
            parsed.query,
            parsed.fragment,
        )
    )


@app.get("/health")
def health():
    """ health check endpoint"""
    return jsonify(
        {
            "success": True,
            "status": "ok",
        }
    ), 200


@app.get("/api/v1/reddit/crawl")
def crawl_reddit():
    """ crawl a reddit url and return the crawler result """
    async def _crawl_and_collect(
            _normalized_url: str,
            _max_amount: int,
            _stop_date: Optional[dt.datetime] = None
    ) -> list[dict[str, Any]]:
        """ crawl a reddit url and return the crawler result """
        crawler = RedditCrawler()
        items: list[dict[str, Any]] = []
        async for post in crawler.crawl(_normalized_url, _max_amount, _stop_date):
            items.append(post.as_dict())
        return items

    loid_cookie: str = request.args.get("loid", "").strip()
    reddit_session: str = request.args.get("reddit_session", "").strip()
    url: str = request.args.get("url", "").strip()
    stop_date: str = request.args.get("stop_date", "").strip()
    max_amount: str = request.args.get("max_amount", "1000").strip().replace(",", '')
    include_comments: bool = request.args.get("include_comments", "true").strip().lower() in {"true", "1", "yes", "on"}
    include_crossposts: bool = request.args.get("include_crossposts", "false").strip().lower() in {"true", "1", "yes", "on"}

    if all([loid_cookie, reddit_session]):
        settings["REDDIT_LOID_COOKIE"] = loid_cookie
        settings["REDDIT_SESSION_COOKIE"] = loid_cookie

        logger.debug(f"set and using custom user cookies")
    else:
        logger.warning("missing cookies detected, defaulting to bot's cookies (could case problems while crawling).")

    if url.count("reddit.com/") > 1:
        return jsonify({
            "success": False,
            "error": "only one reddit link is allowed at a time",
        }), 400
    if not url or len(url) <= 0:
        return jsonify({
            "success": False,
            "error": "missing url parameter or no links provided",
        }), 400

    try: max_amount: int = int(max_amount)
    except ValueError:
        logger.error(f"bad value provided for max_amount:  {request.args.get('max_amount')}")
        return jsonify({
            "success": False,
            "error": "max_amount must be an integer (a number from 1 to 1000)",
        }), 400

    if stop_date:
        try: stop_date: dt.datetime = dt.datetime.strptime(stop_date, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            logger.error(f"bad value provided for stop_date:  {stop_date}")
            return jsonify({
                "success": False,
                "error": "stop_date must be a valid date in YYYY-MM-DD HH:MM:SS format",
            }), 400

    normalized_url: Union[str, bool] = normalize_reddit_json_url(url)
    if not normalized_url:
        return jsonify({
            "success": False,
            "error": "url is refused bad or malformed input",
        }), 400

    settings["INCLUDE_COMMENTS"] = include_comments
    settings["INCLUDE_CROSSPOSTS"] = include_crossposts

    logger.debug(f"crawling link:  {url}  with max_amount:  {max_amount}")

    result = asyncio.run(_crawl_and_collect(normalized_url, max_amount, stop_date))
    if not result:
        return jsonify(
            {
                "success": False,
                "error": "error - something is wrong with the crawler, it did not provide any results.",
                "url": normalized_url.replace(".json", ""),
            }
        ), 501

    return jsonify({
        "success": True,
        "url": normalized_url,
        "result": result,
    }), 200


@app.errorhandler(404)
def not_found(_):
    """ return a JSON 404 response """
    return jsonify({
        "success": False,
        "error": "not found",
    }), 404


@app.errorhandler(405)
def method_not_allowed(_):
    """ return a JSON 405 response """
    return jsonify({
        "success": False,
        "error": "method not allowed",
    }), 405


@app.errorhandler(500)
def internal_error(_):
    """ return a JSON 500 response """
    return jsonify({
        "success": False,
        "error": "internal server error",
    }), 500


if __name__ == "__main__":
    app.run(
        host=settings["API_HOST"],
        port=settings["API_PORT"],
        debug=False,
        load_dotenv=True,
    )
