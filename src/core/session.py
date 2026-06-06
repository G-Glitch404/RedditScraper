import random

from requests import Response
from browserforge.fingerprints import FingerprintGenerator
from curl_cffi.requests import AsyncSession

from core.logger import Logger
from src.settings import settings
from src.util.decorators import retry


class Session(AsyncSession):
    logger = Logger("Session")

    def __init__(self, proxy: list[str] = settings["PROXIES"]) -> None:
        super(Session, self).__init__()
        self.headers.update(self.generate_fingerprint())

        if isinstance(proxy, list):
            if isinstance(proxy, list): proxy = random.choice(proxy)
            self.proxies = {"https": proxy, "http": proxy}  # then we add the proxies after so we check proxies
            self.logger.info(f'proxy: {proxy} is implemented')

        self.logger.info('Session initialized successfully')

    def generate_fingerprint(self, user_agent: str = None) -> dict:
        fingerprint = FingerprintGenerator()
        headers = fingerprint.generate(user_agent=user_agent or self.headers.get('User-Agent')).headers
        return headers

    @retry
    async def request(self, method, url, *args, **kwargs) -> Response:
        """accept http method and forward to parent"""
        kwargs.update({'timeout': 120, 'impersonate': "chrome99", 'verify': True})
        response: Response = await super(Session, self).request(method=method, url=url, *args, **kwargs)
        if not response:
            self.logger.error(f'{method} request failed')
            return Response()
        return response

    async def get(self, *args, **kwargs) -> Response:
        """ GET request with retry decorator """
        return await self.request('GET', *args, **kwargs)
