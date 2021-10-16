import abc
import argparse
import asyncio
import enum
import inspect
import json
import logging
import logging.handlers
import random
import time
import typing
from functools import lru_cache, update_wrapper

import aiohttp
import docstring_parser
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
        return await get(f'{self.__base_url}{method}', params | self.session_params)

    # def method_sync(self, method: str, params: typing.Optional[dict] = None) -> dict:
    #     """
    #     Base method for accessing VK_API (synchronous)
    #
    #     Args:
    #         method: method of VK_API
    #         params: params of request to VK_API
    #
    #     Returns:
    #         JSON-response from VK_API
    #     """
    #     if params is None:
    #         params = dict()
    #     url = f'{self.__base_url}{method}'
    #     params |= self.session_params
    #     return requests.get(url, params).json()

    @property
    def cache(self):
        response = f'Пользователи: {",".join(map(lambda user: user.refer(), self._users_cache.values()))}\n'
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
                                            params=params))['response']['upload_url']
            async with aiohttp.ClientSession() as session:
                resp = await session.post(url=upload_url, data=file)
                photo: dict = json.loads(await resp.text())
            response = (await self.method(method='photos.saveMessagesPhoto', params=photo))['response'][0]
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
        upload_url = upload_url['response']['upload_url']
        async with aiohttp.ClientSession() as session:
            resp = await session.post(url=upload_url, data=file)
            document: dict = json.loads(await resp.text())
        response = (await self.method(method='docs.save',
                                      params=document | {'title': file['file'].name.split('\\')[-1]}))
        response = response['response']
        result = f'{response["type"]}{response["doc"]["owner_id"]}_{response["doc"]["id"]}'
        return result

    _users_cache = {}

    async def get_users(self, users: int | typing.Sequence[int]) -> list['User']:
        if isinstance(users, int):
            users = [users]
        if len(not_cached := [*filter(lambda x: x not in Session._users_cache, users)]) > 0:
            _users = await self.method('users.get',
                                       {'user_ids': ','.join(map(str, not_cached))})
            for user in _users['response']:
                user = User(user['id'], user['first_name'], user['last_name'], self)
                Session._users_cache[user.id] = user
        result = [*{Session._users_cache[user] for user in users}]
        return result

    _chats_cache = {}

    async def get_chat(self, chat_id: int) -> 'Chat':
        """

        Args:
            chat_id: id of chat for this API-token

        Returns:

        """
        if chat_id not in Session._chats_cache:
            result = await self.method('messages.getConversationsById', {'peer_ids': chat_id})
            chat_dict = result['response']['items'][0]
            if chat_dict['peer']['type'] == 'chat':
                chat_dict['admins'] = await self.get_users(
                    [*filter(lambda x: x > 0, [chat_dict['chat_settings']['owner_id'],
                                               *chat_dict['chat_settings']['admin_ids']])])
            Session._chats_cache[chat_id] = Chat(chat_dict, self)
        return Session._chats_cache[chat_id]

    async def get_long_poll_server(self):
        server_config = (await self.method('groups.getLongPollServer'))['response']
        return LongPollServer(self, **server_config)


class User:
    """
    Represent user from VK_API

    Attributes:
        id (int): ID of user
    """

    def __init__(self, user_id: int, first_name: str, last_name: str, session: Session):
        self.session = session
        self.id = user_id
        self.first_name = first_name
        self.last_name = last_name

    def refer(self):
        return f"[id{self.id}|{str(self)}]"

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    def __repr__(self):
        return f'<User {self.first_name} {self.last_name} (id:{self.id})>'

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
        if chat_dict['peer']['type'] == 'chat':
            self.title = chat_dict['chat_settings']['title']
            self.owner = chat_dict['admins'][0]
            self.admins = chat_dict['admins'][1:]
            self.member_count = chat_dict['chat_settings']['members_count']
        else:
            self.title = 'ЛС'

    def __str__(self):
        return self.title

    def __repr__(self):
        return f'<Chat "{self.title}" (id: {self.id})>'

    def __eq__(self, other):
        return isinstance(other, Chat) and self.id == other.id

    def __hash__(self):
        return hash(self.id)

    async def send(self, text: str = '', attachments: list = None, forward_message: dict = None,
                   sticker: typing.Optional[int] = None) -> dict:
        """

        Args:
            text: str
                the text of the message
            attachments: list
                list of the attachments text of the message
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
        if text == '' and (attachments or sticker) is None:
            raise ValueError("Can't send empty message")
        method = 'messages.send'
        params = {
            f'peer_id': self.id,
            f'message': text,
            f'random_id': random.randint(1, 2147123123),
        }
        if sticker is not None:
            params['sticker_id'] = sticker
        if attachments is not None:
            params['attachment'] = attachments
        if forward_message is not None:
            params['forward'] = json.dumps(forward_message)
        return await self.session.method(method=method, params=params)


class Message:
    """
    Representing existing message from VK_API

    Attributes:
        text (str): text of message

    """

    @lru_cache
    def __init__(self, text: str, date: time.struct_time, conversation_message_id: int, sender: User,
                 chat: Chat, vk_session: Session):
        self.vk_session = vk_session
        self.date: time.struct_time = date
        self.text: str = text
        self.sender: User = sender
        self.chat: Chat = chat
        self.conversation_message_id: int = conversation_message_id

    def __str__(self):
        return f'Message from {self.sender}{f" in {self.chat}" if self.chat != "лс" else ""}: {self.text}'

    def __repr__(self):
        return f'<{str(self)}>'

    async def reply(self, text: str = '', attachments: list = None, sticker: typing.Optional[int] = None):
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
            Event.MESSAGE_NEW: self.on_message_new,
            Event.MESSAGE_EDIT: self.on_message_edit,
            Event.MESSAGE_REPLY: self.on_message_reply,
            Event.MESSAGE_ALLOW: self.on_message_allow,
            Event.MESSAGE_DENY: self.on_message_deny,
            # Event.MESSAGE_TYPING_STATE: self.on_message_typing_state,
            Event.MESSAGE_EVENT: self.on_message_event,
            Event.PHOTO_NEW: self.on_photo_new,
            Event.PHOTO_COMMENT_NEW: self.on_photo_comment_new,
            Event.PHOTO_COMMENT_EDIT: self.on_photo_comment_edit,
            Event.PHOTO_COMMENT_RESTORE: self.on_photo_comment_restore,
            Event.PHOTO_COMMENT_DELETE: self.on_photo_comment_delete,
            Event.AUDIO_NEW: self.on_audio_new,
            Event.VIDEO_NEW: self.on_video_new,
            Event.VIDEO_COMMENT_NEW: self.on_video_comment_new,
            Event.VIDEO_COMMENT_EDIT: self.on_video_comment_edit,
            Event.VIDEO_COMMENT_RESTORE: self.on_video_comment_restore,
            Event.VIDEO_COMMENT_DELETE: self.on_video_comment_delete,
            Event.WALL_POST_NEW: self.on_wall_post_new,
            Event.WALL_REPOST: self.on_wall_repost,
            Event.WALL_REPLY_NEW: self.on_wall_reply_new,
            Event.WALL_REPLY_EDIT: self.on_wall_reply_edit,
            Event.WALL_REPLY_RESTORE: self.on_wall_reply_restore,
            Event.WALL_REPLY_DELETE: self.on_wall_reply_delete,
            Event.LIKE_ADD: self.on_like_add,
            Event.LIKE_REMOVE: self.on_like_remove,
            Event.BOARD_POST_NEW: self.on_board_post_new,
            Event.BOARD_POST_EDIT: self.on_board_post_edit,
            Event.BOARD_POST_RESTORE: self.on_board_post_delete,
            Event.BOARD_POST_DELETE: self.on_board_post_delete
        }

    async def __call__(self, event: 'Event', context: dict):
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

    async def on_message_typing_state(self, state, sender: User, receiver):
        pass

    async def on_message_event(self, context):
        pass

    async def on_photo_new(self, context):
        pass

    async def on_photo_comment_new(self, context):
        pass

    async def on_photo_comment_edit(self, context):
        pass

    async def on_photo_comment_restore(self, context):
        pass

    async def on_photo_comment_delete(self, context):
        pass

    async def on_audio_new(self, context):
        pass

    async def on_video_new(self, context):
        pass

    async def on_video_comment_new(self, context):
        pass

    async def on_video_comment_edit(self, context):
        pass

    async def on_video_comment_restore(self, context):
        pass

    async def on_video_comment_delete(self, context):
        pass

    async def on_wall_post_new(self, context):
        pass

    async def on_wall_repost(self, context):
        pass

    async def on_wall_reply_new(self, context):
        pass

    async def on_wall_reply_edit(self, context):
        pass

    async def on_wall_reply_restore(self, context):
        pass

    async def on_wall_reply_delete(self, context):
        pass

    async def on_like_add(self, context):
        pass

    async def on_like_remove(self, context):
        pass

    async def on_board_post_new(self, context):
        pass

    async def on_board_post_edit(self, context):
        pass

    async def on_board_post_restore(self, context):
        pass

    async def on_board_post_delete(self, context):
        pass


class AccessLevel(enum.IntEnum):
    USER = enum.auto()
    ADMIN = enum.auto()
    BOT_ADMIN = enum.auto()
    DEBUG = enum.auto()


class Bot(EventHandler):
    """
    Class, that implements the GroupBot.

    Attributes:

    """

    def __init__(self, access_token: str,
                 group_id, bot_admin: int,
                 session: Session = None,
                 event_server: 'EventServer' = None,
                 log_file='',
                 loglevel=logging.INFO):
        super().__init__()
        log_file = f'logs/{log_file}'
        self.server: EventServer = event_server
        if session is None:
            self.session = GroupSession(access_token=access_token, group_id=group_id)
        else:
            self.session = session
        self.bot_admin: int = bot_admin
        self.commands: CommandHandler = CommandHandler()
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

        @self.command('help')
        async def help_command(message: Message, command: str = ''):
            if command == '':
                a = '\n'
                await message.reply(f'Доступные команды: \n{a.join(map(lambda x: x.name, self.commands))}')
            elif command in self.commands.aliases:
                await message.reply(self.commands[command].help)

    def start(self):
        """
        Function that stars event loop of bot
        """
        if isinstance(self.server, CallBackServer):
            self.server.bind_listener(self)
            self.server.listen()
        else:
            asyncio.run(self.run())

    async def run(self):
        """
        Function that contains main loop
        """
        if self.server is None:
            self.server = await self.session.get_long_poll_server()
        self.server.bind_listener(self)
        await self.server.listen()

    async def on_message_new(self, message: Message, client_info: dict):
        logging.info(message)
        if len(message.text) > 1 and message.text[0] == '!':
            await self.commands.handle_command(message)

    async def on_message_edit(self, message: Message):
        logging.info(
            f'Message edited by {message.sender}) '
            f'in {message.chat.title} '
            f'at {time.strftime("%x %X", message.date)}:\n{message.text}')

    def add_command(self, command: 'Command'):
        self.commands.add_command(command)

    def command(self, name: str = '', names: list[str] = None, access_level: AccessLevel = AccessLevel.USER,
                message_if_deny: str = None, use_doc=False):
        """
        Decorator, that converts function to the Command-object

        Args:
            name: the main name of the command
            names: additional names of the command
            access_level: minimal access level of user to use command
            message_if_deny: text, that will be sent to user if his access_level less than command's access_level
        """

        def wrapper(func) -> 'Command':
            """

            Args:
                func: function that will be converted into Command-object
            Returns:
                Command-object created from function
            """
            self.add_command(command := Command(func, name, names, access_level, message_if_deny, use_doc))
            return command

        return wrapper


class Event(enum.Enum):
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
    def __init__(self, access_token: str, group_id: int, api_version: int = 5.126):
        """

        :param access_token: GROUP_API_TOKEN for VK_API
        :param group_id: id of group you are logging in to
        :param api_version: version af VK_API that you use
        """
        super().__init__(access_token, api_version)
        self.session_params |= {'group_id': group_id}


class Command:
    """
    Class, that added to func-commands features as:\n
    -checking user's permission to use command \n
    -auto-generated help-string for help-command \n
    -auto-replying if access denied \n
    """

    def __init__(self,
                 func: typing.Callable[[Message, ...], typing.Awaitable],
                 name: str = None,
                 names: list[str] = None,
                 access_level: AccessLevel = AccessLevel.USER,
                 message_if_deny: str = 'Access denied',
                 use_doc: bool = False):
        """
        Args:
            func: function that will be converted into Command-object
            name: the main name of the command
            names: additional names of the command
            access_level: minimal access level of user to use command
            message_if_deny: text, that will be sent to user if his access_level less than command's access_level
        """
        if names is None:
            names: list[str] = []
        if name is None or name == '':
            self.name = func.__name__
        else:
            self.name = name
        update_wrapper(self, func)
        self.message_if_deny = message_if_deny
        self._func = func
        self._names = names
        self.access_level = access_level
        parser = argparse.ArgumentParser(description=f'Command {self.name}', exit_on_error=False)
        for name, param in inspect.signature(self).parameters.items():
            if name == 'message':
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
        self.parser = parser
        self.help = self._convert_signature_to_help(use_doc)

    def _check_permissions(self, message: Message) -> bool:
        """
        Checks if user's access_level enough to use command
        Args:
            message: message, witch fires the command

        Returns:

        """
        if message.chat.title == 'ЛС':
            return True
        if message.sender in message.chat.admins:
            user_access_level = AccessLevel.ADMIN
        else:
            user_access_level = AccessLevel.USER
        return user_access_level >= self.access_level

    async def __call__(self, message: Message) -> None:
        if self._check_permissions(message):
            try:
                # self.parser.print_help(sys.stdout)
                args = vars(self.parser.parse_args(message.text.split()[1:]))
                await self._func(message, **args)
            except SystemExit:
                await message.reply(f'Invalid arguments for command {self.name}')
        elif self.message_if_deny:
            await message.reply(self.message_if_deny)

    @property
    def names(self) -> list[str]:
        return [self.name, *self._names]

    def _convert_signature_to_help(self, use_doc: bool = False) -> str:
        """
        Converting the signature of the command function to the help-string, that will be used by standard help-command
        Returns:
            str
            Команда: {name}

            Альтернативные названия: {names} #only if alternative names exists

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
        if len(self._names) > 0:
            res += f'Альтернативные названия: {", ".join(self._names)}' if self._names else ''
        res += '\nАргументы:\n'
        for name, param in inspect.signature(self).parameters.items():
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
    def __init__(self):
        self._aliases: dict[str, Command] = {}

    def add_command(self, command: Command):
        for name in command.names:
            if name in self._aliases:
                raise ValueError(f"Command with alias {name} already exist")
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
        command = temp[0]
        try:
            await self[command](message)
        except KeyError:
            await message.reply(f'There is no command {command}')
        except TypeError as e:
            await message.reply(f'Unexpected arguments for {command} command')
            logging.info(e)


class EventServer(abc.ABC):
    def __init__(self, vk_session: Session):
        self.vk_session = vk_session
        self.listeners: list[EventHandler] = []
        self.tasks: list[asyncio.Task] = []

    def add_task(self, coroutine):
        self.tasks.append(task := asyncio.create_task(coroutine))
        return task

    def bind_listener(self, listener: EventHandler):
        self.listeners.append(listener)

    async def notify_listeners(self, event_dict):
        event, context = await self.parse_event(event_dict)
        for listener in self.listeners:
            await listener(event, context)

    async def parse_event(self, event) -> tuple[Event, dict]:
        event_type: Event = Event[event['type'].upper()]
        context = {}
        match event_type:
            case Event.MESSAGE_NEW:
                message_dict = event['object']['message']
                _wait_users = asyncio.create_task(self.vk_session.get_users(message_dict['from_id']))
                _wait_chat = asyncio.create_task(self.vk_session.get_chat(message_dict['peer_id']))
                context |= {'message': Message(message_dict['text'],
                                               time.localtime(message_dict['date']),
                                               message_dict['conversation_message_id'],
                                               (await _wait_users)[0],
                                               await _wait_chat,
                                               self.vk_session),
                            'client_info': event['object']['client_info']}
        return event_type, context


class CallBackServer(EventServer):
    def __init__(self, vk_session: Session, host='localhost', port=8080):
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
                return web.Response(text='a1d2da46')
            else:
                self.add_task(self.notify_listeners(req))
                return web.Response(text='ok')

        self.app.add_routes([web.post('/', hello_post)])

    def listen(self):
        web.run_app(self.app, host=self.host, port=self.port)
        asyncio.run(asyncio.gather(self.tasks))


class LongPollServer(EventServer):
    def __init__(self, vk_session: Session, server: str, key: str, ts: int):
        super().__init__(vk_session)
        self.server = server
        self.key = key
        self.ts = ts

    # def get_long_poll_server(self):
    #     try:
    #         long_poll_serv = self.vk_session.method_sync('groups.getLongPollServer')['response']
    #         self.server = long_poll_serv['server']
    #         self.key = long_poll_serv['key']
    #         self.ts = long_poll_serv['ts']
    #     except KeyError:
    #         logging.exception("Can't get a LongPollServer")

    async def check(self) -> typing.AsyncIterable[tuple[Event, typing.Dict]]:
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

    async def listen(self) -> None:
        """
        Infinity generator that checking for new events
        Yields:
            tuple
                event and context dictionary
        """
        try:
            while True:
                async for event in self.check():
                    self.add_task(self.notify_listeners(event))
        except Exception as e:
            logging.exception(e)
            await asyncio.gather(self.tasks)

    async def __update(self):
        _new = await self.vk_session.get_long_poll_server()
        self.server = _new.server
        self.key = _new.key
        self.ts = _new.ts
