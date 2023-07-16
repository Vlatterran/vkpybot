import datetime
from abc import abstractmethod
from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from session import Session


class Object(Protocol):
    _session: 'Session'


class User(Object, Protocol):
    id: int


class Message(Object, Protocol):
    text: str
    date: datetime.datetime
    sender: User
    id: int

    @abstractmethod
    def reply(self,
              text: str | None = '',
              attachments: list | None = None,
              sticker: int | None = None): ...


class Chat(Object, Protocol):
    id: int

    @abstractmethod
    def send(self,
             text: str = '',
             attachments: list | None = None,
             forward_message: dict | None = None,
             sticker: int | None = None): ...

    @abstractmethod
    def forward(self,
                messages: list['Message'],
                text: str = '',
                attachments: list | None = None,
                sticker: int | None = None): ...
