import asyncio
import enum
import inspect
import logging
import logging.handlers
import re
import shlex
from argparse import ArgumentParser
from functools import update_wrapper
from typing import Awaitable, Callable, Any

import docstring_parser

from vkpybot.events import EventHandler, EventType
from vkpybot.servers import EventServer, LongPollServer, YandexCloudFunction
from vkpybot.sessions import GroupSession
from vkpybot.types import PrivateChat, Message
from vkpybot.utils import StoreDict


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
                 log_file=None,
                 loglevel=logging.INFO,
                 stdout_log=True,
                 command_prefix='/',
                 server_type='longpoll'):
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
        self._on_startup_async = []
        self._on_startup_sync = []
        if session is None:
            self.session = GroupSession(access_token=access_token)
        else:
            self.session = session
        if event_server is None:
            if server_type == 'longpoll':
                self.server: EventServer = LongPollServer(self.session,
                                                          **self.session.method_sync('groups.getLongPollServer'))
            elif server_type == 'ycf':
                self.server: EventServer = YandexCloudFunction(self.session)
            else:
                raise ValueError('Only longpoll or yvf server_type can be created automatically')

        self.server.bind_listener(self)

        self.command_prefix = command_prefix
        self.bot_admin: int = bot_admin_id
        self.commands: CommandHandler = CommandHandler(bot_admin=bot_admin_id)
        self.regexes: RegexHandler = RegexHandler()
        self.aliases: dict[str, str] = {}
        log_form = "{asctime} - [{levelname}] - ({filename}:{lineno}).{funcName} - {message}"  # noqa
        logging.StreamHandler().setFormatter(logging.Formatter(log_form, style='{'))
        handlers = []
        if stdout_log:
            handlers.append(logging.StreamHandler())
        if log_file is not None:
            handlers.append(logging.handlers.TimedRotatingFileHandler(filename=f'logs/{log_file}',
                                                                      when='midnight',
                                                                      interval=1))
        logging.basicConfig(
            handlers=handlers,
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
        for i in self._on_startup_sync:
            i()
        asyncio.get_event_loop().run_until_complete(asyncio.gather(*(i() for i in self._on_startup_async)))
        self.server.listen()

    def on_startup(self, func):
        if asyncio.iscoroutinefunction(func):
            self._on_startup_async.append(func)
        else:
            self._on_startup_sync.append(func)

    async def on_message_new(self, message: Message, client_info: dict):
        logging.info(message)
        if len(message.text) > 1 and message.text[0] == self.command_prefix:
            result = await self.commands.handle_command(message)
            if isinstance(result, str):
                await self.session.reply(message, result)
        await self.regexes.handle_regex(message)

    async def on_message_edit(self, message: Message):
        logging.info(f'{message} edited at {message.date.strftime("%x %X")}:\n{message.text}')

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
                 use_doc: bool = False,
                 on_event: EventType = EventType.MESSAGE_NEW):
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
            kwargs = {'type': annotation, 'nargs': '?'}
            if param.default is not param.empty:
                kwargs |= {'default': str(param.default)}
            if isinstance(annotation(), dict):
                kwargs['action'] = StoreDict
                kwargs['nargs'] = '+'
                del kwargs['type']
            arg = parser.add_argument(f'{name}',
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
        elif isinstance(message.chat, PrivateChat) or message.sender in message.chat.admins:
            user_access_level = AccessLevel.ADMIN
        else:
            user_access_level = AccessLevel.USER
        return user_access_level >= self.access_level

    async def __call__(self, message: Message) -> str | None:
        if self._check_permissions(message):
            try:
                # self.parser.print_help(sys.stdout)
                args = vars(self.parser.parse_args(shlex.split(message.text)[1:]))
                if self._use_message:
                    args['message'] = message
                if self.__is_coroutine:
                    result = await self._func(**args)
                else:
                    result = self._func(**args)
                return result
            except SystemExit:
                return f'Invalid arguments for command {self.name}'
        elif self.message_if_deny:
            return self.message_if_deny

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
            inspect.Parameter.empty: 'строка',
            dict: 'набор параметров через равно',
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
                res += f'{name} - {annotations[type(param.annotation())]}'
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
            return f'There is no command {_command}'
        try:
            return await command(message)
        except Exception as e:
            logging.exception(e)
            return f'An exception has occurred in "{_command}" execution'


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
