import json

from typing import Any
from curl_cffi.requests import get


def test_api():
    response = get("http://localhost:9092/api/v1/reddit/crawl?url=https://www.reddit.com/r/technology/&max_amount=15", timeout=120)
    try: response_json: dict[str, Any] = response.json()
    except json.decoder.JSONDecodeError:
        print(response.text)
        assert False, "Response is not valid JSON"

    print(response.text)

    for post in response_json["result"]:
        print(post)
        print()

    assert response_json["success"] is True
    assert len(response_json["result"]) > 1
