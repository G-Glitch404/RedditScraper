import datetime as dt
import dataclasses as dc

from typing import Any
from psycopg import sql

from src.core.database import Database
from src.items.item import Item

db = Database()


@dc.dataclass(slots=True)
class Post(Item):
    """ scraper output dataclass """
    thumbnail: str = None
    post_id: str = None
    crosspost_parent: str = None
    publisher_id: str = None
    subreddit_id: str = None
    type: str = None
    subreddit_type: str = None
    title: str = None
    post_flair: str = None
    publisher: str = None
    subreddit: str = None
    published_at: dt.datetime = None
    body: str = None
    sentiment: str = None
    sentiment_score: float = None
    score: int = None
    upvote_ratio: int = None
    upvotes: int = None
    downvotes: int = None
    total_awards: int = None
    total_crossposts: int = None
    total_comments: int = None
    total_subreddit_subs: int = None
    is_hidden: bool = None
    is_crosspost: bool = None
    is_pinned: bool = None
    is_author_premium: bool = None
    is_edited: bool = None
    can_gild: bool = None
    is_comments_still_active: bool = None
    is_score_hidden: bool = None
    is_over_18: bool = None
    is_locked: bool = None
    is_spoiler: bool = None
    is_gallery: bool = None
    is_video: bool = None
    is_original_content: bool = None
    is_crosspostable: bool = None
    is_removed: bool = None
    removed: dict[str, Any] = None
    link: str = None
    found_media: set[str] = None
    comments: list[dict[str, Any]] = None

    def insert_to_db(self, table_name: str = "reddit_posts") -> bool:
        """ inserts the profile items into the Database object """
        fields_, items = [], []
        for item in self:
            fields_.append(item[0])
            items.append(item[1])

        status: bool = db.insert(
            values=tuple(items),
            sql_query=sql.SQL(
                "INSERT INTO {table} ({fields}) VALUES ({vals}) ON CONFLICT (link) DO NOTHING;"
            ).format(
                table=sql.Identifier(table_name),
                fields=sql.SQL(", ").join(map(sql.Identifier, fields_)),
                vals=sql.SQL(", ").join(sql.Placeholder() for _ in fields_)
            )
        )

        return status
