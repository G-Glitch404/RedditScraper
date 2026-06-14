import os
import logging

from dotenv import load_dotenv
from multiprocessing import cpu_count

load_dotenv()


settings = {
    "REDDIT_ENDPOINT": 'https://www.reddit.com',

    "PROXIES": None,
    "VERBOSE": True,
    "LOGGING_LEVEL": logging.DEBUG,

    "API_HOST": os.environ.get("HOST", "0.0.0.0"),
    "API_PORT": int(os.environ.get("PORT", 9092)),
    "CPU_CORES": cpu_count(),

    "MAX_AMOUNT_LIMIT": 1_000,
    "STOP_DATE": None,
    "REDDIT_LOID_COOKIE": os.environ.get("REDDIT_LOID_COOKIE"),
    "REDDIT_SESSION_COOKIE": os.environ.get("REDDIT_SESSION_COOKIE"),
    "DEEP_CRAWL_COMMENTS_SECTION": False,
    "INCLUDE_COMMENTS": True,
    "INCLUDE_CROSSPOSTS": True,

    "DATABASE_ENABLED": False,  # change it if you want to use and store to the database
    "DATABASE": os.environ.get("DATABASE_URL"),  # change per database
}
