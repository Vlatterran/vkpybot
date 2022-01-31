import asyncio
import enum
import functools
import inspect
import json
import logging
import logging.handlers
import re
from abc import ABC, abstractmethod
from argparse import ArgumentParser
from asyncio import Task, run, gather, create_task
from functools import lru_cache, update_wrapper
from random import randint
from time import localtime, strftime, struct_time
from typing import Optional, Awaitable, Dict, AsyncIterable, Sequence, Callable

import aiohttp
import docstring_parser
import pydantic
import requests
from aiohttp import web


async def get(url, params):
    async with aiohttp.ClientSession() as session:
        # proxy='http://proxy.server:3128'
        async with session.get(url, params=params) as resp:
            return await resp.json()


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
                    user = User(**user)
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
                Session._chats_cache[chat_id] = Conversation(chat_dict, self)
            else:
                Session._chats_cache[chat_id] = PrivateChat(chat_dict, self)
        return Session._chats_cache[chat_id]

    async def execute(self, code: str, func_v: int = 1) -> dict:
        return await self.method('execute', {'code': code, 'func_v': func_v})

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

    async def send_message(self,
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
        return await self.method(method, params)


class User(pydantic.BaseModel):
    """
    Represent user from VK_API

    Attributes:
        id (int): ID of user
    """
    id: int
    first_name: str
    last_name: str
    is_closed: bool
    can_access_closed: bool
    deactivated: str | None

    @property
    @functools.lru_cache()
    def refer(self):
        return f"[id{self.id}|{str(self)}]"

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    def __repr__(self):
        return f'<User {str(self)} (id:{self.id})>'

    def __eq__(self, other):
        return isinstance(other, User) and self.id == other.id

    def __hash__(self):
        return hash(self.id)


class Chat:
    """
    Represents chat from VK_API
    """

    def __init__(self, chat_dict, session: Session):
        self.session = session
        self.id = chat_dict['peer']['id']

    def __eq__(self, other):
        return isinstance(other, Chat) and self.id == other.id

    def __hash__(self):
        return hash(self.id)

    async def send(self,
                   text: str = '',
                   attachments: list = None,
                   forward_message: dict = None,
                   sticker: int | None = None) -> dict:
        """
        Shortcut Session.send_message
        Args:
            text:
            attachments:
            forward_message:
            sticker:

        Returns:

        """
        return await self.session.send_message(chat=self,
                                               text=text,
                                               attachments=attachments,
                                               forward_message=forward_message,
                                               sticker=sticker)


class PrivateChat(Chat):
    def __init__(self, chat_dict, session):
        super(PrivateChat, self).__init__(chat_dict, session)

    def __str__(self):
        return 'ЛС'

    def __repr__(self):
        return f'<PrivateChat (id: {self.id})>'


class Conversation(Chat):
    def __init__(self, chat_dict, session):
        super(Conversation, self).__init__(chat_dict, session)
        self.title = chat_dict['chat_settings']['title']
        self.owner = chat_dict['admins'][0]
        self.admins = chat_dict['admins'][1:]
        self.member_count = chat_dict['chat_settings']['members_count']

    def __str__(self):
        return self.title

    def __repr__(self):
        return f'<Conversation "{self.title}" (id: {self.id})>'


class Message:
    """
    Representing existing message from VK_API

    Attributes:
        text (str): text of message

    """

    @lru_cache
    def __init__(self, text: str,
                 date: struct_time,
                 conversation_message_id: int,
                 sender: User,
                 chat: Chat):
        self.date: struct_time = date
        self.text: str = text
        self.sender: User = sender
        self.chat: Chat = chat
        self.conversation_message_id: int = conversation_message_id

    def __str__(self):
        return f'Message from {self.sender}{f" in {self.chat}" if self.chat != "лс" else ""}: {self.text}'

    def __repr__(self):
        return f'<{str(self)}>'

    async def reply(self, text: str = '', attachments: list | None = None, sticker: int | None = None):
        """

        Args:
            text: text of replying message
            attachments: attachments of the replying message
            sticker: sticker

        Returns:

        """
        forward_message = {'peer_id': self.chat.id,
                           'conversation_message_ids': [self.conversation_message_id],
                           'is_reply': 1}

        return await self.chat.send(text=text,
                                    forward_message=forward_message,
                                    attachments=attachments,
                                    sticker=sticker)


class EventHandler:
    """
    Defines handlers for events from VK_API
    More like interface
    """

    def __init__(self):
        self.__event_handler = {
            EventType.MESSAGE_NEW: self.on_message_new,
            EventType.MESSAGE_EDIT: self.on_message_edit,
            EventType.MESSAGE_REPLY: self.on_message_reply,
            EventType.MESSAGE_ALLOW: self.on_message_allow,
            EventType.MESSAGE_DENY: self.on_message_deny,
            EventType.MESSAGE_TYPING_STATE: self.on_message_typing_state,
            EventType.MESSAGE_EVENT: self.on_message_event,
            EventType.PHOTO_NEW: self.on_photo_new,
            EventType.PHOTO_COMMENT_NEW: self.on_photo_comment_new,
            EventType.PHOTO_COMMENT_EDIT: self.on_photo_comment_edit,
            EventType.PHOTO_COMMENT_RESTORE: self.on_photo_comment_restore,
            EventType.PHOTO_COMMENT_DELETE: self.on_photo_comment_delete,
            EventType.AUDIO_NEW: self.on_audio_new,
            EventType.VIDEO_NEW: self.on_video_new,
            EventType.VIDEO_COMMENT_NEW: self.on_video_comment_new,
            EventType.VIDEO_COMMENT_EDIT: self.on_video_comment_edit,
            EventType.VIDEO_COMMENT_RESTORE: self.on_video_comment_restore,
            EventType.VIDEO_COMMENT_DELETE: self.on_video_comment_delete,
            EventType.WALL_POST_NEW: self.on_wall_post_new,
            EventType.WALL_REPOST: self.on_wall_repost,
            EventType.WALL_REPLY_NEW: self.on_wall_reply_new,
            EventType.WALL_REPLY_EDIT: self.on_wall_reply_edit,
            EventType.WALL_REPLY_RESTORE: self.on_wall_reply_restore,
            EventType.WALL_REPLY_DELETE: self.on_wall_reply_delete,
            EventType.LIKE_ADD: self.on_like_add,
            EventType.LIKE_REMOVE: self.on_like_remove,
            EventType.BOARD_POST_NEW: self.on_board_post_new,
            EventType.BOARD_POST_EDIT: self.on_board_post_edit,
            EventType.BOARD_POST_RESTORE: self.on_board_post_delete,
            EventType.BOARD_POST_DELETE: self.on_board_post_delete
        }

    async def __call__(self, event: 'EventType', **context: dict):
        if event in self.__event_handler:
            await self.__event_handler[event](**context)

    async def on_message_new(self, message: Message, client_info: dict):
        pass

    async def on_message_edit(self, message: Message):
        pass

    async def on_message_reply(self, message: Message):
        pass

    async def on_message_allow(self, user: User, key: str):
        pass

    async def on_message_deny(self, user: User):
        pass

    async def on_message_typing_state(self, state: str, sender: User, receiver):
        pass

    async def on_message_event(self, user: User, **context):
        pass

    async def on_photo_new(self, photo, **context):
        pass

    async def on_photo_comment_new(self, comment, photo_id: int, photo_owner_id: int, **context):
        pass

    async def on_photo_comment_edit(self, comment, photo_id: int, photo_owner_id: int, **context):
        pass

    async def on_photo_comment_restore(self, comment, photo_id: int, photo_owner_id: int, **context):
        pass

    # TODO: check if deprecated in VK
    async def on_photo_comment_delete(self, **context):
        pass

    async def on_audio_new(self, audio, **context):
        pass

    async def on_video_new(self, video, **context):
        pass

    async def on_video_comment_new(self, comment, video_id: int, video_owner_id: int, **context):
        pass

    async def on_video_comment_edit(self, comment, video_id: int, video_owner_id: int, **context):
        pass

    async def on_video_comment_restore(self, comment, video_id: int, video_owner_id: int, **context):
        pass

    async def on_video_comment_delete(self, owner_id: int, comment_id: int, user: User, deleter: User, **context):
        pass

    async def on_wall_post_new(self, **context):
        pass

    async def on_wall_repost(self, **context):
        pass

    async def on_wall_reply_new(self, **context):
        pass

    async def on_wall_reply_edit(self, **context):
        pass

    async def on_wall_reply_restore(self, **context):
        pass

    async def on_wall_reply_delete(self, **context):
        pass

    async def on_like_add(self, **context):
        pass

    async def on_like_remove(self, **context):
        pass

    async def on_board_post_new(self, **context):
        pass

    async def on_board_post_edit(self, **context):
        pass

    async def on_board_post_restore(self, **context):
        pass

    async def on_board_post_delete(self, **context):
        pass


class AccessLevel(enum.IntEnum):
    USER = enum.auto()
    ADMIN = enum.auto()
    BOT_ADMIN = enum.auto()


class Bot(EventHandler):
    """
    Class, that implements the GroupBot.

    Attributes:

    """

    def __init__(self, access_token: str,
                 bot_admin_id: int = 0,
                 session: 'GroupSession' = None,
                 event_server: 'EventServer' = None,
                 log_file='',
                 loglevel=logging.INFO):
        """
        Args:
            access_token: API_TOKEN for group
            bot_admin_id: ID of user, who will have maximum access_level
            session:
            event_server:
            log_file:
            loglevel:
        """
        super().__init__()
        log_file = f'logs/{log_file}'
        self.server: EventServer = event_server
        if session is None:
            self.session = GroupSession(access_token=access_token)
        else:
            self.session = session
        self.bot_admin: int = bot_admin_id
        self.commands: CommandHandler = CommandHandler(bot_admin=bot_admin_id)
        self.regexes: RegexHandler = RegexHandler()
        self.aliases: dict[str, str] = {}
        log_form = "{asctime} - [{levelname}] - ({filename}:{lineno}).{funcName} - {message}"  # noqa
        logging.StreamHandler().setFormatter(logging.Formatter(log_form, style='{'))
        logging.basicConfig(
            handlers=[logging.StreamHandler(),
                      logging.handlers.TimedRotatingFileHandler(filename=log_file,
                                                                when='midnight',
                                                                interval=1)],
            level=loglevel,
            format=log_form,
            style='{',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # logging.getLogger().addHandler(logging.StreamHandler())
        # logging.getLogger().addHandler(logging.handlers.TimedRotatingFileHandler(filename=log_file,
        #                                                                          when='midnight',
        #                                                                          interval=1))

        # TODO: Add RegexHandler to the help
        @self.command('help')
        def help_command(command: str = ''):
            if command == '':
                a = '\n'
                return f'Доступные команды: \n{a.join([x.short_help for x in self.commands])}'
            elif command in self.commands.aliases:
                return self.commands[command].help
            else:
                return f"Command \"{command}\" doesn't exist"

    def start(self):
        """
        Function that stars event loop of bot
        """
        if self.server is None:
            self.server = LongPollServer(self.session,
                                         **self.session.method_sync('groups.getLongPollServer'))
        self.server.bind_listener(self)
        self.server.listen()

    async def on_message_new(self, message: Message, client_info: dict):
        logging.info(message)
        if len(message.text) > 1 and message.text[0] == '!':
            await self.commands.handle_command(message)
        await self.regexes.handle_regex(message)

    async def on_message_edit(self, message: Message):
        logging.info(f'{message} edited at {strftime("%x %X", message.date)}:\n{message.text}')

    def add_command(self, command: 'Command'):
        self.commands.add_command(command)

    def add_regex(self, regex: 'Regex'):
        self.regexes.add_regex(regex)

    def command(self,
                name: str = '',
                names: list[str] = None,
                access_level: AccessLevel = AccessLevel.USER,
                message_if_deny: str = None,
                use_doc=False):
        """
        Decorator, that converts function to the Command-object

        Args:
            name: the main name of the command
            names: additional aliases of the command
            access_level: minimal access level of user to use command
            message_if_deny: text, that will be sent to user if his access_level less than command's access_level
            use_doc:
        """

        def wrapper(func: Callable[[...], Awaitable] | Callable[[...], str | None]) -> 'Command':
            """

            Args:
                func: function that will be converted into Command-object
            Returns:
                Command-object created from function
            """
            kwargs = {}
            if message_if_deny is not None:
                kwargs['message_if_deny'] = message_if_deny
            self.add_command(command := Command(func, name, names, access_level, use_doc=use_doc, **kwargs))
            return command

        return wrapper

    def regex(self, regular_expression: str):
        def wrapper(func):
            self.add_regex(regex := Regex(func, regular_expression))
            return regex

        return wrapper


class EventType(enum.Enum):
    """
    Represents events from VK_BOT_API
    """
    # message events
    MESSAGE_NEW = enum.auto()

    MESSAGE_REPLY = enum.auto()
    MESSAGE_EDIT = enum.auto()

    MESSAGE_ALLOW = enum.auto()

    MESSAGE_DENY = enum.auto()

    MESSAGE_TYPING_STATE = enum.auto()

    MESSAGE_EVENT = enum.auto()

    # photo events
    PHOTO_NEW = enum.auto()

    PHOTO_COMMENT_NEW = enum.auto()
    PHOTO_COMMENT_EDIT = enum.auto()
    PHOTO_COMMENT_RESTORE = enum.auto()

    PHOTO_COMMENT_DELETE = enum.auto()

    # audio events
    AUDIO_NEW = enum.auto()

    # video events
    VIDEO_NEW = enum.auto()

    VIDEO_COMMENT_NEW = enum.auto()
    VIDEO_COMMENT_EDIT = enum.auto()
    VIDEO_COMMENT_RESTORE = enum.auto()

    VIDEO_COMMENT_DELETE = enum.auto()

    # wall events
    WALL_POST_NEW = enum.auto()
    WALL_REPOST = enum.auto()

    WALL_REPLY_NEW = enum.auto()
    WALL_REPLY_EDIT = enum.auto()
    WALL_REPLY_RESTORE = enum.auto()

    WALL_REPLY_DELETE = enum.auto()

    # like events
    LIKE_ADD = enum.auto()

    LIKE_REMOVE = enum.auto()

    # board events
    BOARD_POST_NEW = enum.auto()
    BOARD_POST_EDIT = enum.auto()
    BOARD_POST_RESTORE = enum.auto()

    BOARD_POST_DELETE = enum.auto()


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

    async def get_long_poll_server_row(self):
        server_config = (await self.method('groups.getLongPollServer'))
        return server_config


class Command:
    """
    Class, that added to func-commands features as:
    -checking user's permission to use command
    -auto-generated help-string for help-command
    -auto-replying if access denied
    """

    def __init__(self,
                 func: Callable[[...], Awaitable] | Callable[[...], str | None],
                 name: str = None,
                 aliases: list[str] = None,
                 access_level: AccessLevel = AccessLevel.USER,
                 message_if_deny: str = 'Access denied',
                 use_doc: bool = False):
        """
        Args:
            func: function that will be converted into Command-object
            name: the main name of the command
            aliases: additional names of the command
            access_level: minimal access level of user to use command
            message_if_deny: text, that will be sent to user if his access_level less than command's access_level
        """
        self.bot_admin = 0
        if aliases is None:
            aliases: list[str] = []
        if name is None or name == '':
            self.name = func.__name__
        else:
            self.name = name
        update_wrapper(self, func)
        self.message_if_deny = message_if_deny
        self._func = func
        self.aliases = aliases
        self.access_level = access_level
        parser = ArgumentParser(description=f'Command {self.name}', exit_on_error=False)
        self._use_message = False
        for name, param in inspect.signature(self).parameters.items():
            if name == 'message':
                self._use_message = True
                continue
            annotation = param.annotation
            if param.annotation is param.empty:
                annotation = str
                # {"-" if parameter.default is not parameter.empty else ""}
            kwargs = {}
            if param.default is not param.empty:
                kwargs |= {'default': str(param.default)}
            arg = parser.add_argument(f'{name}',
                                      type=annotation,
                                      nargs='?',
                                      **kwargs
                                      )
            # print(arg)
        # parser.print_help(sys.stdout)
        self.__is_coroutine = asyncio.iscoroutinefunction(func)
        self.parser = parser
        self.names = [self.name, *self.aliases]
        self.help = self._convert_signature_to_help(use_doc)
        self.short_help = self.name + (f'({", ".join(self.aliases)})' if self.aliases else '')

    def _check_permissions(self, message: Message) -> bool:
        """
        Checks if user's access_level enough to use command
        Args:
            message: message, witch fires the command

        Returns:

        """
        if message.sender.id == self.bot_admin:
            user_access_level = AccessLevel.BOT_ADMIN
        elif message.chat.title == 'ЛС' or message.sender in message.chat.admins:
            user_access_level = AccessLevel.ADMIN
        else:
            user_access_level = AccessLevel.USER
        return user_access_level >= self.access_level

    async def __call__(self, message: Message) -> None:
        if self._check_permissions(message):
            try:
                # self.parser.print_help(sys.stdout)
                args = vars(self.parser.parse_args(message.text.split()[1:]))
                if self._use_message:
                    args['message'] = message
                if self.__is_coroutine:
                    result = await self._func(**args)
                else:
                    result = self._func(**args)
                if isinstance(result, str):
                    await message.reply(result)
            except SystemExit:
                await message.reply(f'Invalid arguments for command {self.name}')
        elif self.message_if_deny:
            await message.reply(self.message_if_deny)

    def _convert_signature_to_help(self, use_doc: bool = False) -> str:
        """
        Converting the signature of the command function to the help-string, that will be used by standard help-command

        Returns:

            Команда: {name}

            Альтернативные названия: {aliases} #only if alternative aliases exists

            Аргументы:

            {name of the argument} - {type of argument} (значение по умолчанию: {default value of the argument})

            #if default value don't exist, brackets won't be added#
        """
        annotations = {
            str: 'строка',
            int: 'целое число',
            float: 'действительное число',
            inspect.Parameter.empty: 'строка'
        }
        if use_doc and self.__doc__ is not None:
            documentation = docstring_parser.parse(self.__doc__)
        else:
            documentation = False
        res = f'Команда: {self.name}\n'
        if documentation:
            res += f'{documentation.short_description}\n'
        if len(self.aliases) > 0:
            res += f'Альтернативные названия: {", ".join(self.aliases)}' if self.aliases else ''
        if params := inspect.signature(self).parameters.items():
            res += '\nАргументы:\n'
            for name, param in params:
                if name == 'message':
                    continue
                # print(param.annotation)
                res += f'{name} - {annotations[param.annotation]}'
                if param.default is not param.empty:
                    res += f' (значение по умолчанию: {param.default!r})'
                if documentation:
                    res += f'\n{[*filter(lambda x: x.arg_name == name, documentation.params)][0].description}'
                res += '\n'

        return res


class CommandHandler:
    def __init__(self, bot_admin):
        self.bot_admin = bot_admin
        self._aliases: dict[str, Command] = {}

    def add_command(self, command: Command):
        for name in command.names:
            if name in self._aliases:
                raise ValueError(f"Command with alias {name} already exist")
        command.bot_admin = self.bot_admin
        for name in command.names:
            self._aliases[name] = command

    @property
    def commands(self) -> set[Command]:
        return set(self._aliases.values())

    @property
    def aliases(self):
        return self._aliases.keys()

    def __getitem__(self, item: str) -> Command:
        return self._aliases[item]

    def __iter__(self):
        return iter(self.commands)

    async def handle_command(self, message: Message):
        temp = message.text[1:].split()
        _command = temp[0]
        try:
            command = self[_command]
        except KeyError:
            await message.reply(f'There is no command {_command}')
            return
        try:
            await command(message)
        except Exception as e:
            await message.reply(f'An exception has occurred in "{_command}" execution')
            logging.exception(e)


class Regex:
    def __init__(self, func: Callable[[Message], Awaitable], regular_expression: str):
        self.regex = re.compile(regular_expression)
        update_wrapper(self, func)
        self._func = func

    async def __call__(self, message: Message):
        if re.match(self.regex, message.text):
            await self._func(message)


class RegexHandler:
    def __init__(self):
        self.regexes = []

    def add_regex(self, regex: Regex):
        self.regexes.append(regex)

    async def handle_regex(self, message: Message):
        tasks = []
        for r in self.regexes:
            tasks.append(asyncio.create_task(r(message)))
        for t in tasks:
            await t


class EventServer(ABC):
    def __init__(self, vk_session: GroupSession):
        self.vk_session = vk_session
        self.listeners: list[EventHandler] = []
        self.tasks: list[Task] = []

    def create_task(self, coroutine):
        self.tasks.append(task := create_task(coroutine))
        return task

    def bind_listener(self, listener: EventHandler):
        self.listeners.append(listener)

    async def _notify_listeners(self, event_dict):
        event, context = await self.parse_event(event_dict)
        for listener in self.listeners:
            await listener(event, **context)

    def notify_listeners(self, event_dict):
        self.create_task(self._notify_listeners(event_dict))

    async def parse_event(self, event) -> tuple[EventType, dict]:
        event_type: EventType = EventType[event['type'].upper()]
        context = {}
        match event_type:
            case EventType.MESSAGE_NEW:
                message_dict = event['object']['message']
                _wait_user = create_task(self.vk_session.get_user(message_dict['from_id']))
                _wait_chat = create_task(self.vk_session.get_chat(message_dict['peer_id']))
                context |= {'message': Message(message_dict['text'],
                                               localtime(message_dict['date']),
                                               message_dict['conversation_message_id'],
                                               (await _wait_user),
                                               await _wait_chat),
                            'client_info': event['object']['client_info']}
        return event_type, context

    @abstractmethod
    def listen(self):
        pass


class CallBackServer(EventServer):
    def __init__(self, vk_session: GroupSession, host='localhost', port=8080):
        super().__init__(vk_session)
        self.host = host
        self.port = port
        self.app = web.Application()

        async def hello_post(request: web.Request):
            req = await request.json()
            print(req)
            if req['type'] == 'confirmation':
                code = (await self.vk_session.method('groups.getCallbackConfirmationCode'))['response']['code']
                print(code)
                return web.Response(text=code)
            else:
                self.notify_listeners(req)
                return web.Response(text='ok')

        self.app.add_routes([web.post('/', hello_post)])

    def listen(self):
        web.run_app(self.app, host=self.host, port=self.port)
        run(gather(self.tasks))


class LongPollServer(EventServer):
    def __init__(self, vk_session: GroupSession, server: str, key: str, ts: int):
        super().__init__(vk_session)
        self.server = server
        self.key = key
        self.ts = ts

    async def check(self) -> AsyncIterable[tuple[EventType, Dict]]:
        """
        Checks for new events on long_poll_server, updates long_poll_server information if failed to get events

        Yields:
            tuple
                event and context dictionary
        """
        result = None
        retries = 0
        while result is None:
            try:
                params = {'act': 'a_check',
                          'key': self.key,
                          'ts': self.ts,
                          'wait': 25}
                result = await get(self.server, params)
            except Exception:
                logging.exception(f'try {(retries := retries + 1)}')

        if 'failed' in result:
            error_code = result['failed']
            if error_code == 1:
                logging.debug('Updating ts')
                self.ts = result['ts']
            elif error_code in (2, 3):
                logging.info('Updating long_poll_server')
                await self.__update()
            else:
                logging.error(f'Unexpected error_code code: {error_code} in {result}')
        else:
            self.ts = result['ts']
            events = result['updates']
            for event in events:
                yield event

    def listen(self) -> None:
        run(self._listen())

    async def _listen(self) -> None:
        try:
            while True:
                async for event in self.check():
                    self.notify_listeners(event)
        except Exception as e:
            logging.exception(e)
            await gather(self.tasks)

    async def __update(self):
        new = await self.vk_session.get_long_poll_server_row()
        self.server = new['server']
        self.key = new['key']
        self.ts = new['ts']
