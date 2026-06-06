import os
import logging

from multiprocessing import cpu_count
from dotenv import load_dotenv

load_dotenv()


settings = {
    "reddit_ENDPOINT": "https://www.reddit.com",

    "PROXIES": None,
    "VERBOSE": True,
    "LOGGING_LEVEL": logging.DEBUG,
    "CPU_CORES": cpu_count(),

    "DATABASE": os.environ["DATABASE_URL"],  # change per database
}
