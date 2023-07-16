from asyncio import Task
from typing import Optional, overload, Sequence, Awaitable, Iterable

from vkpybot import User, Chat, Message
from vkpybot.connection import Connection
from vkpybot.session import JSON


class Manager:
    _connection: Connection

    def __init__(self, connection: Connection): ...

    async def method(self, method: str, params: dict[str, str]) -> JSON: ...


class UsersManager(Manager):
    queue: dict[str, set[int]]
    _inflight: dict[str, tuple[Optional[Task], Optional[Task]]]
    _users_cache: dict

    async def _get(self) -> list[dict]: ...

    @overload
    async def get(self, users: Sequence[int]) -> list[User]: ...

    @overload
    async def get(self, users: int) -> User: ...


class ChatsManager(Manager):
    queue: dict[str, set[int]]
    _inflight: dict[str, tuple[Optional[Task], Optional[Task]]]
    _users_cache: dict

    async def _get(self) -> list[dict]: ...

    @overload
    async def get(self, users: Sequence[int]) -> list[Chat]: ...

    @overload
    async def get(self, users: int) -> Chat: ...


class MessagesManager(Manager):
    def send(self,
             chat: Chat,
             text: Optional[str],
             attachments: Optional[list],
             forward_message: Optional[dict],
             sticker: Optional[int]
             ) -> Awaitable: ...

    def reply(self,
              message: Message,
              text: Optional[str] = '',
              attachments: Optional[list] = None,
              sticker: Optional[int] = None
              ) -> Awaitable: ...

    def forward(self,
                messages: Iterable[Message],
                chat: Chat,
                text: Optional[str],
                attachments: Optional[list],
                sticker: Optional[int]
                ) -> Awaitable: ...
