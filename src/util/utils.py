import os
from typing import Callable, Any, Union, Optional

pagination: Callable[[dict], dict[str, str]] = lambda payload: {"after": extract(payload, "data", "after")}


def normalize_url(reddit_url: str) -> str:
    """ normalize a reddit url to a standard format """
    url_parts: list[str] = reddit_url.strip().split("?", 1)
    url: str = (url_parts[0].replace('/.json', '') + '/.json').replace('//', '/')
    url: str = url.replace('https:/', '').replace('http:/', '')
    if url.startswith('/'): url: str = url[1:]

    return ('https://' + url) + (f'?{url_parts[1]}' if len(url_parts) > 1 else '')


def extract(item: Any, *index: Union[str, int], default: Optional[Any] = None) -> Any:
    """ recursively extract data from a nested list based on the given indices """
    try:
        match len(index):
            case 0: return item
            case 1: return item[index[0]]
            case _: return extract(item[index[0]], *index[1:])
    except (IndexError, TypeError, KeyError): return default


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
