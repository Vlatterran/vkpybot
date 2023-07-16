import json
from typing import TYPE_CHECKING, Any, Coroutine, Awaitable

import aiohttp

from vkpybot.connection import Connection
from vkpybot.manager import MessagesManager, UsersManager
from vkpybot.types import Chat

if TYPE_CHECKING:
    from vkpybot.server import LongPollServer


class Session:
    """
    Class for accessing VK_API as user
    """

    def __init__(self, access_token: str, api_version: float = 5.126):
        """
        Args:
            access_token:
                USER_API_TOKEN for VK_API
            api_version:
                version af VK_API that you use
        """
        connection = Connection(access_token, api_version)
        self._connection: Connection = connection
        self.users: UsersManager = UsersManager(connection)
        self.messages: MessagesManager = MessagesManager(connection)

    @property
    def cache(self):
        response = f'Пользователи: {",".join(map(lambda user: user.refer, self.users._users_cache.values()))}\n'
        response += f'Чаты: {[*self._chats_cache.values()]}\n'
        response += f'Изображения: {[*self._image_cache.values()]}'
        return response

    _image_cache: dict = {}

    async def upload_image(self, image: str) -> str:
        """
        Uploads the image to the hidden album, saves it and returns the attachment-sting of the image
        Args:
            image (str): path to the image
        Returns:
             image as the attachment
        """
        with open(image, 'rb') as photo:
            file = {'photo': photo}
            if file['photo'] not in self._image_cache:
                params: dict[str, Any] = {
                    'peer_id': 0
                }
                upload_url = (await self._connection.method(method=f'photos.getMessagesUploadServer',
                                                            params=params))['upload_url']
                async with aiohttp.ClientSession() as session:
                    resp = await session.post(url=upload_url, data=file)
                    photo: dict = json.loads(await resp.text())
                response = (await self._connection.method(method='photos.saveMessagesPhoto', params=photo))[0]
                self._image_cache[file['photo']] = f'photo{response["owner_id"]}_{response["id"]}'
            return self._image_cache[file['photo']]

    async def upload_document(self, doc: str, chat: 'Chat') -> str:
        """
        Uploads the image to the hidden album, saves it and returns the attachment-sting of the image
        Args:
            chat: chat where document will be sent
            doc (str): path to the document
        Returns:
             document as the attachment
        """
        params = {
            'peer_id': chat.id
        }
        file = {'file': open(doc, mode='rb')}
        resp = (await self._connection.method(method='docs.getMessagesUploadServer',
                                                    params=params))
        upload_url: str = resp['upload_url']
        async with aiohttp.ClientSession() as session:
            resp = await session.post(url=upload_url, data=file)
            document: dict = json.loads(await resp.text())
        response = (await self._connection.method(method='docs.save',
                                                  params=document | {'title': file['file'].name.split('\\')[-1]}))
        result = f'{response["type"]}{response["doc"]["owner_id"]}_{response["doc"]["id"]}'
        return result


class GroupSession(Session):
    """
    Class to accessing VK_API as group
    """

    def __init__(self, access_token: str, api_version: float = 5.126):
        """

        Args:
            access_token: GROUP_API_TOKEN for VK_API
            api_version: version af VK_API that you use
        """
        super().__init__(access_token, api_version)
        self._connection.params.update({'group_id': self._connection.method_sync('groups.getById')[0]['id']})

    async def get_long_poll_server(self) -> LongPollServer:
        return LongPollServer(self, **await self.get_long_poll_server_row())

    def get_long_poll_server_row(self) -> Awaitable[dict[str, Any]]:
        return self._connection.method('groups.getLongPollServer')
