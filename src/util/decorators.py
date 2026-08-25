import json

from functools import wraps
from typing import Any, Callable

from src.core.logger import Logger

retry_logger = Logger("Retry")
catch_logger = Logger('ExceptionsHandler')


def catch_exceptions(func, exceptions: tuple = (Exception, json.decoder.JSONDecodeError)) -> Callable:
    """ decorator for catching selenium exceptions """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try: return func(*args, **kwargs)
        except exceptions as e:
            catch_logger.exception(f'function "{func.__name__}" failed with exception "{e}" and parameters: "{args, kwargs}"')
            return False

    return wrapper
