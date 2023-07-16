import abc
import asyncio
import functools
import json
import logging
from random import randint

from vkpybot import User, Message
from vkpybot.connection import Connection

class Manager(abc.ABC):
    def __init__(self, connection: Connection):
        self._connection = connection

    @functools.wraps(Connection.method)
    def method(self, method, params=None):
        return self._connection.method(method, params)

    @functools.wraps(Connection.method)
    def method_sync(self, method, params=None):
        return self._connection.method_sync(method, params)


class MessagesManager(Manager):
    def send(self,
             chat,
             text='',
             attachments=None,
             forward_message=None,
             sticker=None):
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
              text: str | None = '',
              attachments=None,
              sticker: int | None = None):
        forward_message = {'peer_id': message.chat.id,
                           'conversation_message_ids': [message.id],
                           'is_reply': 1}
        return self.send(chat=message.chat,
                         text=text,
                         forward_message=forward_message,
                         attachments=attachments,
                         sticker=sticker)

    def forward(self,
                messages,
                chat,
                text='',
                attachments=None,
                sticker=None):
        forward_message = {'peer_id': chat.id,
                           'conversation_message_ids': [message.id for message in messages],
                           'is_reply': 0}

        return self.send(chat=chat,
                         text=text,
                         forward_message=forward_message,
                         attachments=attachments,
                         sticker=sticker)

    async def get_by_conversation_message_id(self, chat_id: int,
                                             message_ids: int | list[int],
                                             extended: bool = False):
        logging.warning('This method is in early beta and could not work')
        params = {
            'peer_ids': chat_id,
            'conversation_message_ids': [message_ids] if isinstance(message_ids, int) else list(message_ids),
            'extended': int(extended)
        }
        ids = params['conversation_message_ids']
        code = f'''
    var messages = API.messages.getByConversationsMessageId({{"conversation_message_ids": {ids}, 'peer_id':{chat_id}}});
    var chats = API.messages.getConversationById({{
        "group_id": {self._connection._params['group_id']},
        "peer_ids": messages.items@.peer_id
    }});
    var user_ids = chats.items@.chat_settings@.owner_id.concat(chats.items@.chat_settings@.admin_ids);
    var users = API.users.get({{"user_ids":user_ids}});
    return {{"message":messages.items[0],
        "chat":chats.items[0],
        "users":users,
        "user": user_ids}};
            '''
        a = await self._connection.execute(code)
        return a


class UsersManager(Manager):
    def __init__(self, connection):
        super().__init__(connection)
        self._users_cache = {}
        self.queue = {'get': set()}
        self._inflight = {
            'get': (None, None)
        }

    async def _get(self) -> list[dict]:
        await asyncio.sleep(.3)
        ids = self.queue['get']
        self.queue['get'] = set()
        task = asyncio.create_task(self.method('users.get', {'user_ids': ','.join(map(str, ids))}))
        self._inflight['get'] = self._inflight['get'][0], task
        res = await task
        self._inflight['get'] = None, None
        if not isinstance(res, list):
            raise RuntimeError('Unnexpected result from "users.get"')
        return res

    async def get(self, users):
        if len(not_cached := (set(users) - self._users_cache.keys())) > 0:
            if self._inflight['get'][0] is None or self._inflight['get'][1] is not None:
                self.queue['get'].update(not_cached)
                task = asyncio.create_task(self._get())
                self._inflight['get'] = (task, None)
                _users = await task
                for user in _users:
                    user = User(user, session=...)
                    self._users_cache[user.id] = user
            else:
                self.queue['get'].update(not_cached)
                await self._inflight['get'][0]
        result = [*{self._users_cache[user] for user in users}]
        return result


class ChatsManager(Manager):
    def __init__(self, connection):
        super().__init__(connection)
        self._chat_cache = {}
        self.queue = {'get': set()}
        self._inflight = {
            'get': (None, None)
        }

    async def _get(self) -> list[dict]:
        await asyncio.sleep(.3)
        ids = self.queue['get']
        self.queue['get'] = set()
        task = asyncio.create_task(self.method('messages.getConversationsById', {'user_ids': ','.join(map(str, ids))}))
        self._inflight['get'] = self._inflight['get'][0], task
        res = await task
        self._inflight['get'] = None, None
        if not isinstance(res, list):
            raise RuntimeError('Unnexpected result from "users.get"')
        return res

    async def get(self, chat: int):
        if len(not_cached := ({chat} - self._users_cache.keys())) > 0:
            if self._inflight['get'][0] is None or self._inflight['get'][1] is not None:
                self.queue['get'].update(not_cached)
                task = asyncio.create_task(self._get())
                self._inflight['get'] = (task, None)
                _users = await task
                for user in _users:
                    user = User(user, session=...)
                    self._users_cache[user.id] = user
            else:
                self.queue['get'].update(not_cached)
                await self._inflight['get'][0]
        result = [*{self._c[user] for user in users}]
        return result

    # if chat_id not in Session._chats_cache:
    #     result = await self.method('messages.getConversationsById', {'peer_ids': chat_id})
    #     chat_dict = result['items'][0]
    #     if chat_dict['peer']['type'] == 'chat':
    #         chat_dict['admins'] = await self.get_users(
    #             [*filter(lambda x: x > 0, [chat_dict['chat_settings']['owner_id'],
    #                                        *chat_dict['chat_settings']['admin_ids']])])
    #         chat_cls = Conversation
    #     else:
    #         chat_cls = PrivateChat
    #     Session._chats_cache[chat_id] = chat_cls(chat_dict, session=self)
    # return Session._chats_cache[chat_id]

