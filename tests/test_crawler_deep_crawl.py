from src.settings import settings

import time
from src.RedditCrawler import RedditCrawler


async def test_scrape_post() -> None:
    link: str = ""
    total_comments = 0
    settings["CRAWL_COMMENTS_SECTION"] = True
    start = time.time()

    crawler = RedditCrawler()
    async for post in crawler.crawl(link):
        assert post["post_id"]
        assert post["body"]
        assert post["link"]

        for k, v in post:
            print(f"{k}: {v}")
            if k != 'comments' or not isinstance(v, list): continue
            print(f"len comments: {len(v)}\n")
            total_comments += len(v)

            for reply in v:
                for reply_k, reply_v in reply.items():
                    print(f"{reply_k}: {reply_v}")
                    if reply_k != 'replies' or not isinstance(reply_v, list): continue
                    total_comments += len(reply_v)
                    print(f"len_2: {len(reply_v)}\n")

    assert total_comments >= 200
    end = time.time()
    print("\nOperation took: ", round((end-start), 2), f' secs and total comments: {total_comments}')
