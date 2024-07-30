import json
import time
import logging
from functools import wraps
from logger.logger import Logger
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    ElementClickInterceptedException,
    ElementNotInteractableException,
)

execution_timer_logger = Logger(logging.getLogger('ExecutionTimer'), {})
retry_logger = Logger(logging.getLogger('Retry'), {})
catch_logger = Logger(logging.getLogger('ExceptionsHandler'), {})


def catch_exceptions(
        func,
        exceptions: tuple = (
                Exception,
                NoSuchElementException,
                StaleElementReferenceException,
                ElementClickInterceptedException,
                ElementNotInteractableException
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


def execution_timer(func, retries: int = 3, interval: int = 30):
    """ wait interval seconds for cool down and retry on failure """
    @catch_exceptions
    def wrapper(*args, **kwargs):
        execution_timer_logger.debug(f'waiting {interval} seconds for cool down')
        for _ in range(retries):
            time.sleep(interval)
            func_return = func(*args, **kwargs)
            if func_return: return func_return
            else: execution_timer_logger.debug(f'function {func} failed with bad output retrying after {interval} seconds')

        return func(*args, **kwargs)  # if failure keeps occurring, return it

    return wrapper
