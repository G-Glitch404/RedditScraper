import datetime as dt
import dataclasses as dc

from typing import Any
from psycopg import sql
from core.database import Database

db = Database()


@dc.dataclass(slots=True)
class Item(object):
    def get(self, key: str) -> Any:
        """ get attribute value """
        return getattr(self, key)

    def as_dict(self) -> dict:
        return dc.asdict(self)

    def __iter__(self):
        for f in dc.fields(self):
            yield f.name, getattr(self, f.name)

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def __setitem__(self, key: str, value: Any):
        setattr(self, key, value)

    def __str__(self) -> str:
        return str(dc.asdict(self))

    def __hash__(self):
        return hash(
            tuple(self)
        )


@dc.dataclass(slots=True)
class Post(Item):
    """ scraper output dataclass """
    thumbnail: str = None
    title: str = None
    publisher: str = None
    publisher_id: str = None
    flairs: str = None
    awards: int = None
    comments: int = None
    subreddit: str = None
    subbreddit_id: str = None
    score: int = None
    type: str = None
    body: str = None
    link: str = None
    published: dt.datetime = None
    modified: dt.datetime = None
    is_over_18: bool = None
    is_original_content: bool = None
    is_crosspostable: bool = None
    is_removed: dict[str, Any] = None
    authors: list[dict[str, Any]] = None
    videos_urls: list[str] = None
    images_urls: list[str] = None
    replies: list[dict[str, Any]] = None

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

    def __add__(self, other):
        return Post(
            **{**dc.asdict(self), **dc.asdict(other)}
        )


@dc.dataclass(slots=True)
class Comment(Item):
    score: int = None
    type: str = None
    body: str = None
    link: str = None
    is_over_18: bool = None
    published: dt.datetime = None
    modified: dt.datetime = None
    replies: list[dict[str, Any]] = None

    def __add__(self, other):
        return Post(
            **{**dc.asdict(self), **dc.asdict(other)}
        )
