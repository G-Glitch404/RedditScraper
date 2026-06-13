import os
import re
import datetime as dt

from typing import Callable, Any, Union, Optional

DEFAULT_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"

pagination: Callable[[dict], dict[str, str]] = lambda payload: {"after": extract(payload, "data", "after")}
today: Callable[[], dt.date] = lambda: dt.datetime.now(tz=dt.timezone.utc).date()
clean_text: Callable[[Any], str] = lambda text: re.sub('\n+|\\s+|\\t+|\\r+|\\r\\n+|\\r\\n', ' ', ''.join(text)).strip()


def normalize_url(reddit_url: str) -> str:
    """ normalize a reddit url to a standard format """
    url: str = reddit_url.strip().split("?", 1)[0]
    url: str = (url.replace('/.json', '') + '/.json').replace('//', '/')
    url: str = url.replace('https:/', '').replace('http:/', '')
    if url.startswith('/'): url: str = url[1:]

    return 'https://' + url


def extract(item: Any, *index: Union[str, int], default: Optional[Any] = None) -> Any:
    """ recursively extract data from a nested list based on the given indices """
    try:
        match len(index):
            case 0: return item
            case 1: return item[index[0]]
            case _: return extract(item[index[0]], *index[1:])
    except (IndexError, TypeError, KeyError): return default


def to_datetime_aware(dt_obj: dt.datetime | dt.date | str, formate: str = DEFAULT_DATE_FORMAT) -> dt.datetime:
    """ convert date or datetime to an aware utc datetime """
    if isinstance(dt_obj, str):
        dt_obj: dt.datetime = dt.datetime.strptime(dt_obj, DEFAULT_DATE_FORMAT)

    if isinstance(dt_obj, dt.date) and not isinstance(dt_obj, dt.datetime):
        dt_obj: dt.datetime = dt.datetime.combine(dt_obj, dt.datetime.min.time())

    if dt_obj.tzinfo is None or dt_obj.utcoffset() is None or dt_obj.tzname() != 'UTC':
        return dt_obj.replace(tzinfo=dt.timezone.utc)

    return dt.datetime.strptime(dt_obj, formate)


def path(file_path: str, secondary_path: str = None) -> str:
    """ converts a relative path to an absolute path """
    seperator: str = '\\' if 'nt' in os.name.lower() else '/'
    file: str = os.path.join(
        seperator.join(
            os.path.realpath(
                os.path.join(
                    os.getcwd(),
                    os.path.dirname(__file__)
                )
            ).split(seperator)[:-1]),  # remove the current folder from path
        file_path
    )

    return file if secondary_path is None else os.path.join(file, secondary_path)
