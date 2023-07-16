import datetime
from typing import Protocol, Optional, Awaitable, Iterable

from vkpybot.session import Session, JSON


class MessangerObject(Protocol):
    ...


class VKObject:
    _session: Session

    def __init__(self, *, session: Session): ...


class User(VKObject):
    id: int
    first_name: str
    last_name: str
    is_closed: bool
    can_access_closed: bool
    refer: str

    def __init__(self, usr: dict, *, session: Session): ...

    def __str__(self) -> str: ...


class Message(VKObject):
    date: datetime.datetime
    text: str
    sender: User
    chat: Chat
    id: int
    def __init__(self, msg: dict, *, session: Session): ...

    def reply(self):
        ...


class Chat(VKObject):
    id: int
    def __init__(self, chat_dict: dict, *, session: Session): ...

    def send(self,
             text: Optional[str],
             attachments: Optional[list],
             forward_message: Optional[dict],
             sticker: Optional[int]) -> Awaitable[JSON]: ...



    def forward(self,
                messages: Iterable[Message],
                chat: Chat,
                text: Optional[str],
                attachments: Optional[list],
                sticker: Optional[int]
                ) -> Awaitable: ...

class PrivateChat(Chat):
    ...

class Conversation(Chat):
    title: str
    owner: User
    admins: list[User]
    member_count: int

