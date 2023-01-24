import asyncio
import json
import typing
from functools import lru_cache
from random import randint
from typing import Optional, Sequence

import aiohttp
import requests

from vkpybot.types import Chat, User, Conversation, PrivateChat, Message
from vkpybot.utils import get

if typing.TYPE_CHECKING:
    from vkpybot.servers import LongPollServer


class Session:
    """
    Class for accessing VK_API as user
    """
    __base_url = 'https://api.vk.com/method/'

    def __init__(self, access_token: str, api_version: float = 5.126):
        """
        Args:
            access_token:
                USER_API_TOKEN for VK_API
            api_version:
                version af VK_API that you use
        """
        self.session_params: dict = {'access_token': access_token,
                                     'v': api_version}

    async def method(self, method: str, params: dict = None) -> dict:
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
        # logging.debug(f'(request){self.__base_url}{method}, {params | self.session_params | {"access_token": ""} }')
        resp = (await get(f'{self.__base_url}{method}', params | self.session_params))
        # logging.debug(f'(response){resp}')
        if 'error' in resp:
            raise Exception(f"code {resp['error']['error_code']}: {resp['error']['error_msg']}")
        return resp['response']

    def method_sync(self, method: str, params: Optional[dict] = None) -> dict:
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
        url = f'{self.__base_url}{method}'
        params |= self.session_params
        resp = requests.get(url, params).json()
        if 'error' in resp:
            raise Exception(f"code {resp['error']['error_code']}: {resp['error']['error_msg']}")
        return resp['response']

    @property
    def cache(self):
        response = f'Пользователи: {",".join(map(lambda user: user.refer, self._users_cache.values()))}\n'
        response += f'Чаты: {[*self._chats_cache.values()]}\n'
        response += f'Изображения: {[*self._image_cache.values()]}'
        return response

    _image_cache = {}

    async def upload_image(self, image: str) -> str:
        """
        Uploads the image to the hidden album, saves it and returns the attachment-sting of the image
        Args:
            image (str): path to the image
        Returns:
             image as the attachment
        """
        file = {'photo': open(image, 'rb')}
        if file['photo'] not in Session._image_cache:
            params = {
                'peer_id': 0
            }
            upload_url = (await self.method(method=f'photos.getMessagesUploadServer',
                                            params=params))['upload_url']
            async with aiohttp.ClientSession() as session:
                resp = await session.post(url=upload_url, data=file)
                photo: dict = json.loads(await resp.text())
            response = (await self.method(method='photos.saveMessagesPhoto', params=photo))[0]
            Session._image_cache[file['photo']] = f'photo{response["owner_id"]}_{response["id"]}'
        return Session._image_cache[file['photo']]

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
        upload_url = (await self.method(method='docs.getMessagesUploadServer',
                                        params=params))
        upload_url = upload_url['upload_url']
        async with aiohttp.ClientSession() as session:
            resp = await session.post(url=upload_url, data=file)
            document: dict = json.loads(await resp.text())
        response = (await self.method(method='docs.save',
                                      params=document | {'title': file['file'].name.split('\\')[-1]}))
        result = f'{response["type"]}{response["doc"]["owner_id"]}_{response["doc"]["id"]}'
        return result

    class GetUsersRequest:
        def __init__(self, users: Sequence[int], session: 'Session'):
            self.user_ids = users
            self.session = session

        def add_request(self, users: Sequence[int]):
            self.user_ids += users

        async def __call__(self):
            await asyncio.sleep(.3)
            return await self.session.method('users.get', {'user_ids': ','.join(map(str, self.user_ids))})

    _users_cache = {}
    _get_user_request: GetUsersRequest = None
    _get_user_request_task: asyncio.Task = None

    async def get_users(self, users: Sequence[int]) -> list['User']:
        if len(not_cached := [*filter(lambda x: x not in Session._users_cache, users)]) > 0:
            if Session._get_user_request_task is None:
                Session._get_user_request = Session.GetUsersRequest(not_cached, self)
                Session._get_user_request_task = asyncio.create_task(Session._get_user_request())
                _users = await Session._get_user_request_task
                for user in _users:
                    user = User(user, session=self)
                    Session._users_cache[user.id] = user
                Session._get_user_request_task = None
            else:
                Session._get_user_request.add_request(not_cached)
                await Session._get_user_request_task
        result = [*{Session._users_cache[user] for user in users}]
        return result

    async def get_user(self, user: int) -> 'User':
        return (await self.get_users([user]))[0]

    _chats_cache = {}

    async def get_chat(self, chat_id: int) -> 'Chat':
        """

        Args:
            chat_id: id of chat for this API-token

        Returns:

        """
        if chat_id not in Session._chats_cache:
            result = await self.method('messages.getConversationsById', {'peer_ids': chat_id})
            chat_dict = result['items'][0]
            if chat_dict['peer']['type'] == 'chat':
                chat_dict['admins'] = await self.get_users(
                    [*filter(lambda x: x > 0, [chat_dict['chat_settings']['owner_id'],
                                               *chat_dict['chat_settings']['admin_ids']])])
                chat_cls = Conversation
            else:
                chat_cls = PrivateChat
            Session._chats_cache[chat_id] = chat_cls(chat_dict, session=self)
        return Session._chats_cache[chat_id]

    def execute(self, code: str, func_v: int = 1):
        return self.method('execute', {'code': code, 'func_v': func_v})

    async def get_by_conversation_message_id(self, chat_id: int,
                                             message_ids: int | list[int],
                                             extended: bool = False):
        params = {
            'peer_ids': chat_id,
            'conversation_message_ids': [message_ids] if isinstance(message_ids, int) else list(message_ids),
            'extended': int(extended)
        }
        ids = params['conversation_message_ids']
        code = f'''
var messages = API.messages.getByConversationsMessageId({{"conversation_message_ids": {ids}, 'peer_id':{chat_id}}});
var chats = API.messages.getConversationById({{
    "group_id": {self.session_params['group_id']},
    "peer_ids": messages.items@.peer_id
}});
var user_ids = chats.items@.chat_settings@.owner_id.concat(chats.items@.chat_settings@.admin_ids);
var users = API.users.get({{"user_ids":user_ids}});
return {{"message":messages.items[0],
    "chat":chats.items[0],
    "users":users,
    "user": user_ids}};
        '''
        from pprint import pprint
        print(code)
        print(await self.method('messages.getConversationsById', params))
        pprint(a := await self.execute(code))
        return a

    def send_message(self,
                     chat: 'Chat',
                     text: str = '',
                     attachments: list = None,
                     forward_message: dict = None,
                     sticker: int | None = None):
        """
            Args:
                chat: Chat
                text: str
                    the text of the message
                attachments: list of the attachments text of the message
                forward_message: dict
                sticker: id of sticker in message (sticker will replace text)
                    {
                        'peer_id': int,
                        'conversation_message_ids': list[int],
                        Optional['is_reply']: 1 if replying (only if forwarding to one message in same chat)
                    }

            Returns:
                dict:
                    {
                        'peer_id': 'идентификатор назначения',
                        'message_id': 'идентификатор сообщения',
                        'conversation_message_id': 'идентификатор сообщения в диалоге',
                        'error': 'сообщение об ошибке, если сообщение не было доставлено получателю'
                    }
        """
        method = 'messages.send'
        if text == '' and (attachments or sticker) is None:
            raise ValueError("Can't send empty message")
        params = {
            f'peer_id': chat.id,
            f'message': text,
            f'random_id': randint(1, 2147123123),
        }
        if sticker is not None:
            params['sticker_id'] = sticker
        if attachments is not None:
            params['attachment'] = attachments
        if forward_message is not None:
            params['forward'] = json.dumps(forward_message)
        return self.method(method, params)

    def reply(self,
              message: 'Message',
              text: str = '',
              attachments: list | None = None,
              sticker: int | None = None):
        """

        Args:
            message: message to reply
            text: text of replying message
            attachments: attachments of the replying message
            sticker: sticker

        Returns:

        """
        forward_message = {'peer_id': message.chat.id,
                           'conversation_message_ids': [message.conversation_message_id],
                           'is_reply': 1}

        return self.send_message(chat=message.chat,
                                 text=text,
                                 forward_message=forward_message,
                                 attachments=attachments,
                                 sticker=sticker)

    def forward(self,
                messages: list['Message'],
                chat: 'Chat',
                text: str = '',
                attachments: list | None = None,
                sticker: int | None = None):
        """

        Args:
            messages: message to reply
            chat: where to send message
            text: text of replying message
            attachments: attachments of the replying message
            sticker: sticker

        Returns:

        """
        forward_message = {'peer_id': chat.id,
                           'conversation_message_ids': [message.conversation_message_id for message in messages],
                           'is_reply': 0}

        return self.send_message(chat=chat,
                                 text=text,
                                 forward_message=forward_message,
                                 attachments=attachments,
                                 sticker=sticker)


class GroupSession(Session):
    """
    Class to accessing VK_API as group
    """

    @lru_cache
    def __init__(self, access_token: str, api_version: float = 5.126):
        """

        Args:
            access_token: GROUP_API_TOKEN for VK_API
            api_version: version af VK_API that you use
        """
        super().__init__(access_token, api_version)
        self.session_params |= {'group_id': self.method_sync('groups.getById')[0]['id']}

    async def get_long_poll_server(self):
        return LongPollServer(self, **await self.get_long_poll_server_row())

    def get_long_poll_server_row(self):
        return self.method('groups.getLongPollServer')
