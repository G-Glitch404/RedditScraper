import asyncio
from typing import Union, Any, AsyncGenerator

from flask import Flask, jsonify, request
from urllib.parse import urlparse, urlunparse

from src.RedditCrawler import RedditCrawler
from src.core.logger import Logger
from src.items.post import Post

logger = Logger("CrawlerAPI")
app = Flask(__name__)
crawler = RedditCrawler()

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

    netloc = parsed.netloc.lower()
    if not parsed.scheme or not parsed.netloc or netloc not in ALLOWED_NETLOCS:
        logger.error(f'malformed or bad input  -  url: "{url}"')
        return False

    path = parsed.path or "/"
    if path.endswith(".json"):
        normalized_path = path
    else:
        normalized_path = path.rstrip("/") + "/.json"

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
    async def _collect_async_generator(gen: AsyncGenerator) -> list[Any]:
        """ run and collect an AsyncGenerator object """
        items = []
        async for item in gen:
            items.append(item)
        return items

    url: str = request.args.get("url", "").strip()

    if not url:
        return jsonify({
            "success": False,
            "error": "missing url parameter",
        }), 400

    normalized_url: Union[str, bool] = normalize_reddit_json_url(url)
    if not normalized_url:
        return jsonify({
            "success": False,
            "error": "url is refused bad or malformed input",
        }), 400

    result: AsyncGenerator[Post, None] = crawler.crawl(normalized_url)
    result: list[Post] = asyncio.run(_collect_async_generator(result))
    if not result:
        return jsonify(
            {
                "success": False,
                "error": "crawler is did not provide any results.",
                "url": normalized_url,
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
    app.run(host="0.0.0.0", port=8000, debug=False)
