import asyncio
import time
import random

from collections import deque

from requests import Response
from browserforge.fingerprints import FingerprintGenerator
from curl_cffi.requests import AsyncSession

from src.core.logger import Logger
from src.settings import settings
from src.util.decorators import catch_exceptions


class Session(AsyncSession):
    """
     using this Session class usually cookies are not passed to the request headers
     you have to update your object Session().headers to use {"Cookie": cookie1=abcd;cookie2=abcd}
     instead of using Session.cookies

     and this is a bug that needs to be fixed later
    """
    logger = Logger("Session")

    def __init__(self, proxy: list[str] = settings["PROXIES"]) -> None:
        super().__init__()
        self.headers.update(self.generate_fingerprint())

        if isinstance(proxy, list):
            if isinstance(proxy, list): proxy: str = random.choice(proxy)
            self.proxies.update({"https": proxy, "http": proxy})
            self.logger.info(f'proxy: {proxy} is implemented')

        self._request_count: int = 0
        self._request_timestamps: deque[float] = deque(maxlen=100)  # Keep last 100 request times
        self._rate_limit_lock = asyncio.Lock()

        self.logger.info('Session initialized successfully')

    async def _respect_rate_limit(self) -> None:
        async with self._rate_limit_lock:
            now = time.monotonic()

            while self._request_timestamps and now - self._request_timestamps[0] >= 60:
                self._request_timestamps.popleft()

            if len(self._request_timestamps) >= 100:
                wait_for = 60 - (now - self._request_timestamps[0])
                if wait_for > 0:
                    self.logger.info(f"rate limit reached, sleeping for {wait_for:.2f} seconds then continuing")
                    await asyncio.sleep(wait_for)

                now = time.monotonic()
                while self._request_timestamps and now - self._request_timestamps[0] >= 60:
                    self._request_timestamps.popleft()

            self._request_timestamps.append(time.monotonic())

    def generate_fingerprint(self, user_agent: str = None) -> dict:
        """ generates headers and user-agent for the session """
        fingerprint = FingerprintGenerator()
        headers = fingerprint.generate(user_agent=user_agent or self.headers.get('User-Agent')).headers
        return headers

    @catch_exceptions
    async def request(self, method, url, *args, **kwargs) -> Response:
        """ accept http method and forward to parent """
        await self._respect_rate_limit()

        kwargs.update({
            'method': method,
            'url': url,
            'headers': self.headers,
            'cookies': self.cookies,
            'timeout': 120,
            'impersonate': "chrome99",
            'verify': True,
        })

        response: Response = await super(Session, self).request(*args, **kwargs)
        if not response:
            self.logger.error(f'{method} request failed')
            return Response()

        return response

    async def get(self, url: str, *args, **kwargs) -> Response:
        """ GET request with retry decorator """
        return await self.request('GET', url, *args, **kwargs)
