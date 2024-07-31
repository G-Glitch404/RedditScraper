import json
import time
import logging
from functools import wraps
from logger import Logger

retry_logger = Logger(logging.getLogger('Retry'), {})
catch_logger = Logger(logging.getLogger('ExceptionsHandler'), {})


def catch_exceptions(
        func,
        exceptions: tuple = (
                Exception,
                json.decoder.JSONDecodeError,
            )
        ):
    """ decorator for catching selenium exceptions """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try: return func(*args, **kwargs)
        except exceptions as e:
            catch_logger.error(f'function {func} failed with exception: {e}')
            return False

    return wrapper


def retry(
        func,
        retries: int = 3,
        interval: int = 1,
        exceptions: tuple = (Exception, json.decoder.JSONDecodeError)):
    """ decorator for retrying a function after failure """
    @wraps(func)
    def wrapper(*args, **kwargs):
        for _ in range(retries):
            try: return func(*args, **kwargs)
            except exceptions as e:
                retry_logger.debug(f'function {func} failed with exception {e}')
            finally: time.sleep(interval)
        return func(*args, **kwargs)  # if error keeps occurring, return it

    return wrapper
