import weakref
from typing import overload, Any, Awaitable

import aiohttp
import requests

from vkpybot.session import JSON


class Connection:
    _base_url: str
    _finalizer: weakref.finalize
    _async_session: aiohttp.ClientSession
    _sync_session: requests.Session
    _params: dict

    @property
    def params(self) -> dict: ...
    @property
    def closed(self) -> dict: ...


    def __init__(self, access_token: str, api_version: float): ...

    @overload
    async def method(self, method: str) -> JSON: ...

    @overload
    async def method(self, method: str, params: dict[str, Any]) -> JSON: ...

    @overload
    def method_sync(self, method: str) -> JSON: ...

    @overload
    def method_sync(self, method: str, params: dict[str, Any]) -> JSON: ...

    def _finalize(self): ...

    def close(self): ...

    @overload
    def execute(self, code: str, func_v: int) -> Awaitable[JSON]: ...

    @overload
    def execute(self, code: str): ...


