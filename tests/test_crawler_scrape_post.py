import json
import time
from src.RedditCrawler import RedditCrawler


async def test_scrape_post() -> None:
    link: str = "https://www.reddit.com/r/mildlyinfuriating/comments/1u680uv/some_ahole_ran_over_my_mailbox_today/"
    total_comments = 0
    start = time.time()

    crawler = RedditCrawler()
    async for post in crawler.crawl(link):
        print(post)
        json.dump(post.as_dict(), open("post.json", "w"), indent=2, ensure_ascii=False)

        assert post["post_id"]
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

    assert total_comments >= 70
    end = time.time()
    print("\nOperation took: ", round((end-start), 2), f' secs and total comments: {total_comments}')


if __name__ == '__main__':
    import asyncio
    asyncio.run(test_scrape_post())
