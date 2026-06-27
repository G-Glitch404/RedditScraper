import json
import time
import pytest
import datetime as dt

from src.RedditCrawler import RedditCrawler


@pytest.mark.asyncio
async def test_scrape_post() -> None:
    link: str = ""
    total_posts: int = 0
    start: float = time.time()

    crawler = RedditCrawler()
    posts: list[dict] = []
    async for post in crawler.crawl(link, max_amount=5000, stop_date=dt.datetime.now(tz=dt.timezone.utc) - dt.timedelta(days=31)):
        total_posts += 1
        for k, v in post:
            print(f"{k}: {v}")
        print('\n')
        posts.append(post.as_dict())

    json.dump(posts, open('posts.json', "w"), indent=2, ensure_ascii=False)
    assert total_posts >= 100
    end: float = time.time()
    print("\nOperation took: ", round((end-start), 2), f' secs and total comments: {total_posts}')
