import datetime
from abc import abstractmethod
from session import Session as Session
from typing import Protocol

class Object(Protocol): ...

class User(Object, Protocol):
    id: int

class Message(Object, Protocol):
    text: str
    date: datetime.datetime
    sender: User
    id: int
    @abstractmethod
    def reply(self, text: str | None = ..., attachments: list | None = ..., sticker: int | None = ...): ...

class Chat(Object, Protocol):
    id: int
    @abstractmethod
    def send(self, text: str = ..., attachments: list | None = ..., forward_message: dict | None = ..., sticker: int | None = ...): ...
    @abstractmethod
    def forward(self, messages: list['Message'], text: str = ..., attachments: list | None = ..., sticker: int | None = ...): ...
