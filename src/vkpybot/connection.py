import weakref

import aiohttp
import requests


class Connection:
    _base_url = 'https://api.vk.com/method/'

    def __init__(self, access_token, api_version=5.126):
        """
        Args:
            access_token:
                USER_API_TOKEN for VK_API
            api_version:
                version af VK_API that you use
        """
        self._params: dict = {'access_token': access_token,
                              'v': api_version}
        self._async_session = aiohttp.ClientSession(self._base_url)
        self._sync_session = requests.Session()
        self._finalizer = weakref.finalize(self, self._finalize)

    def close(self):
        self._finalizer()

    @property
    def closed(self):
        return self._finalizer.alive

    def _finalize(self):
        self._sync_session.close()
        self._async_session.close()

    async def method(self, method, params=None) -> dict | list:
        """
        Base method for accessing VK_API (asynchronous)

        Args:
            method:
                method of VK_API
            params:
                params of request to VK_API
        Returns:
            JSON-response from VK_API
        """
        if params is None:
            params = {}
        # logging.debug(f'(request){self.__base_url}{method}, {params | self._session_params | {"access_token": ""} }')
        resp = await (await self._async_session.get(f'{self._base_url}{method}',
                                                    params=params | self.params)).json()
        # logging.debug(f'(response){resp}')
        if 'error' in resp:
            raise Exception(f"code {resp['error']['error_code']}: {resp['error']['error_msg']}")
        return resp['response']

    def method_sync(self, method, params=None) -> dict:
        """
        Base method for accessing VK_API (synchronous)

        Args:
            method: method of VK_API
            params: params of request to VK_API

        Returns:
            JSON-response from VK_API
        """
        if params is None:
            params = dict()
        url = f'{self._base_url}{method}'
        params |= self.params
        resp = self._sync_session.get(url, params=params).json()
        if 'error' in resp:
            raise Exception(f"code {resp['error']['error_code']}: {resp['error']['error_msg']}")
        return resp['response']

    def execute(self, code, func_v=1):
        return self.method('execute', {'code': code, 'func_v': func_v})

    @property
    def params(self):
        return self._params

