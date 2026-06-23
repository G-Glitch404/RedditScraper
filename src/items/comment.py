import datetime as dt
import dataclasses as dc

from src.items.item import Item


@dc.dataclass(slots=True)
class Comment(Item):
    author: str = None
    author_id: str = None
    parent_id: str = None
    comment_id: str = None
    link_id: str = None
    subreddit_id: str = None
    subreddit: str = None
    sentiment: str = None
    sentiment_score: int = None
    score: int = None
    upvotes: int = None
    downvotes: int = None
    upvotes_ratio: int = None
    type: str = None
    body: str = None
    link: str = None
    unrepliable_reason: str = None
    can_send_replies: bool = None
    is_removed: bool = None
    is_post_comment: bool = None
    is_reply: bool = None
    is_score_hidden: bool = None
    is_over_18: bool = None
    is_edited: bool = None
    is_author_blocked: bool = None
    published_at: dt.datetime = None
    # replies: list = None  # disabled until future update
