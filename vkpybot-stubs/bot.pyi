import enum
import re
from argparse import ArgumentParser
from typing import Awaitable, Callable, Any

from vkpybot.events import EventHandler as EventHandler, EventType as EventType
from vkpybot.server import EventServer as EventServer
from vkpybot.session import GroupSession as GroupSession
from vkpybot.types import Message as Message


class AccessLevel(enum.IntEnum):
    USER: int
    ADMIN: int
    BOT_ADMIN: int


class Bot(EventHandler):
    session: GroupSession
    server: EventServer
    command_prefix: str
    bot_admin: int
    commands: CommandHandler
    regexes: RegexHandler
    aliases: dict[str, str]

    def __init__(self,
                 access_token: str,
                 bot_admin_id: int = ...,
                 session: GroupSession = ...,
                 event_server: EventServer = ...,
                 log_file: Incomplete | None = ...,
                 loglevel=...,
                 stdout_log: bool = ...,
                 command_prefix: str = ...,
                 server_type: str = ...) -> None: ...

    def start(self) -> None: ...

    def on_startup(self, func) -> None: ...

    async def on_message_new(self, message: Message, client_info: dict): ...

    async def on_message_edit(self, message: Message): ...

    def add_command(self, command: Command): ...

    def add_regex(self, regex: Regex): ...

    def command(self,
                name: str = ...,
                names: list[str] = ...,
                access_level: AccessLevel = ...,
                message_if_deny: str = ...,
                use_doc: bool = ...): ...

    def regex(self, regular_expression: str): ...


class Command:
    bot_admin: int
    name: str
    message_if_deny: str
    aliases: list[str]
    access_level: AccessLevel
    parser: ArgumentParser
    names: list[str]
    help: str
    short_help: str
    _use_message: bool
    _func_async: Callable[[Any], Awaitable[str | None]] | None
    _func_sync: Callable[[Any], str | None] | None
    _on_startup_async: list[Callable[[None], Awaitable[None]]] = []
    _on_startup_sync: list[Callable[[None], None]] = []

    def __init__(self, func: Callable[[...], Awaitable[str | None]] | Callable[[...], str | None],
                 name: str = ...,
                 aliases: list[str] = ...,
                 access_level: AccessLevel = ...,
                 message_if_deny: str = ...,
                 use_doc: bool = ...,
                 on_event: EventType = ...) -> None:         ...

    async def __call__(self, message: Message) -> str | None: ...

    def _check_permissions(self, message: Message): ...

    def _convert_signature_to_help(self, use_doc: bool): ...

    def _get_access_level(self, message) -> AccessLevel: ...


class CommandHandler:
    bot_admin: int
    _aliases: dict[str, Command]

    def __init__(self, bot_admin: int) -> None: ...

    def add_command(self, command: Command): ...

    @property
    def commands(self) -> set[Command]: ...

    @property
    def aliases(self) ->: ...

    def __getitem__(self, item: str) -> Command: ...

    def __iter__(self): ...

    async def handle_command(self, message: Message): ...


class Regex:
    regex: re.Pattern
    _func: Callable[[Message], Awaitable[None]]

    def __init__(self, func: Callable[[Message], Awaitable], regular_expression: str) -> None: ...

    async def __call__(self, message: Message): ...


class RegexHandler:
    regexes: list[Regex]

    def __init__(self): ...

    def add_regex(self, regex: Regex): ...

    async def handle_regex(self, message: Message): ...
