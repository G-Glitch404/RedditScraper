import os
import logging
from dotenv import load_dotenv

load_dotenv()


settings = {
    "PROXIES": None,
    "VERBOSE": True,
    "LOGGING_LEVEL": logging.DEBUG,

    "MAX_AMOUNT_LIMIT": 1_000,
    "CRAWL_COMMENTS_SECTION": False,

    "DATABASE": os.environ["DATABASE_URL"],  # change per database
}
