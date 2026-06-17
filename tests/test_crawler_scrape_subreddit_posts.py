import pytest
import time

from src.RedditCrawler import RedditCrawler
from src.settings import settings


@pytest.mark.asyncio
async def test_scrape_post() -> None:
    link: str = "https://www.reddit.com/r/AskReddit/"
    total_posts: int = 0
    settings["MAX_AMOUNT_LIMIT"] = 100
    start: float = time.time()

    crawler = RedditCrawler()
    async for post in crawler.crawl(link, max_amount=settings["MAX_AMOUNT_LIMIT"]):
        total_posts += 1
        for k, v in post:
            print(f"{k}: {v}")
        print('\n')

    assert total_posts >= 85
    end: float = time.time()
    print("\nOperation took: ", round((end-start), 2), f' secs and total comments: {total_posts}')
