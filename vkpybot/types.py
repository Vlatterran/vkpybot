import datetime
import functools

import pydantic


class User(pydantic.BaseModel):
    """
    Represent user from VK_API

    Attributes:
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

    def __init__(self, chat_dict):
        self.id = chat_dict['peer']['id']

    def __eq__(self, other):
        return isinstance(other, Chat) and self.id == other.id

    def __hash__(self):
        return hash(self.id)


class PrivateChat(Chat):
    def __init__(self, chat_dict):
        super(PrivateChat, self).__init__(chat_dict)

    def __str__(self):
        return 'ЛС'

    def __repr__(self):
        return f'<PrivateChat (id: {self.id})>'


class Conversation(Chat):
    def __init__(self, chat_dict):
        super(Conversation, self).__init__(chat_dict)
        self.title = chat_dict['chat_settings']['title']
        self.owner = chat_dict['admins'][0]
        self.admins = chat_dict['admins'][1:]
        self.member_count = chat_dict['chat_settings']['members_count']

    def __str__(self):
        return self.title

    def __repr__(self):
        return f'<Conversation "{self.title}" (id: {self.id})>'


class Message(pydantic.BaseModel):
    """
    Representing existing message from VK_API

    """

    date: datetime.datetime
    text: str
    sender: User
    chat: Chat
    conversation_message_id: int

    class Config:
        arbitrary_types_allowed = True

    def __str__(self):
        in_chat = f" in {self.chat}" if isinstance(self.chat, Conversation) else ""
        return f'Message from {self.sender}{in_chat}: {self.text}'

    def __repr__(self):
        return f'<{str(self)}>'
