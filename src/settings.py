import os
import logging

from dotenv import load_dotenv
from multiprocessing import cpu_count
from src.util.utils import today

load_dotenv()


settings = {
    "REDDIT_ENDPOINT": 'https://www.reddit.com',

    "PROXIES": None,
    "VERBOSE": True,
    "LOGGING_LEVEL": logging.DEBUG,
    "CPU_CORES": cpu_count(),

    "MAX_AMOUNT_LIMIT": 1_000,
    "CRAWL_COMMENTS_SECTION": False,

    "REDDIT_LOID_COOKIE": os.environ["REDDIT_LOID_COOKIE"],
    "REDDIT_SESSION_COOKIE": os.environ["REDDIT_SESSION_COOKIE"],

    "TODAY": today(),

    "DATABASE_ENABLED": False,  # change it if you want to use and store to the database
    "DATABASE": os.environ["DATABASE_URL"],  # change per database
}
