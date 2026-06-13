import random

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
        super(Session, self).__init__()
        self.headers.update(self.generate_fingerprint())

        if isinstance(proxy, list):
            if isinstance(proxy, list): proxy: str = random.choice(proxy)
            self.proxies.update({"https": proxy, "http": proxy})
            self.logger.info(f'proxy: {proxy} is implemented')

        self.logger.info('Session initialized successfully')

    def generate_fingerprint(self, user_agent: str = None) -> dict:
        """ generates headers and user-agent for the session """
        fingerprint = FingerprintGenerator()
        headers = fingerprint.generate(user_agent=user_agent or self.headers.get('User-Agent')).headers
        return headers

    @catch_exceptions
    async def request(self, method, url, *args, **kwargs) -> Response:
        """ accept http method and forward to parent """
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

    async def get(self, url: str, **kwargs) -> Response:
        """ GET request with retry decorator """
        return await self.request('GET', url, **kwargs)
