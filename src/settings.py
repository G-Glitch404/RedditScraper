import os
import logging

import datetime as dt

from dotenv import load_dotenv
from src.util.utils import to_datetime_aware

load_dotenv()


settings = {
    "REDDIT_ENDPOINT": 'https://www.reddit.com',

    "PROXIES": None,
    "VERBOSE": True,
    "LOGGING_LEVEL": logging.DEBUG,

    "MAX_AMOUNT_LIMIT": 1_000,
    "CRAWL_COMMENTS_SECTION": False,

    "TODAY": to_datetime_aware(dt.datetime.now()),

    "DATABASE": os.environ["DATABASE_URL"],  # change per database
}
