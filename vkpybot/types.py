import datetime
import functools
import typing

if typing.TYPE_CHECKING:
    from sessions import Session


class VKObject:
    def __init__(self, *, session: 'Session'):
        self._session = session


class User(VKObject):
    """
    Represent user from VK_API
    """

    def __init__(self, usr: dict, *, session: 'Session'):
        super().__init__(session=session)
        self.id: int = int(usr['id'])
        self.first_name: str = usr['first_name']
        self.last_name: str = usr['last_name']
        self.is_closed: bool = bool(usr['is_closed'])
        self.can_access_closed: bool = bool(usr['can_access_closed'])

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


class Chat(VKObject):
    """
    Represents chat from VK_API
    """

    def __init__(self, chat_dict, *, session: 'Session'):
        super().__init__(session=session)
        self.id = chat_dict['peer']['id']

    def __eq__(self, other):
        return isinstance(other, Chat) and self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def send(self,
             text: str = '',
             attachments: list = None,
             forward_message: dict = None,
             sticker: int | None = None):
        return self._session.send_message(self, text, attachments, forward_message, sticker)

    def forward(self,
                messages: list['Message'],
                text: str = '',
                attachments: list | None = None,
                sticker: int | None = None):
        return self._session.forward(messages, self, text, attachments, sticker)


class PrivateChat(Chat):
    def __init__(self, chat_dict, *, session: 'Session'):
        super().__init__(chat_dict, session=session)

    def __str__(self):
        return 'ЛС'

    def __repr__(self):
        return f'<PrivateChat (id: {self.id})>'


class Conversation(Chat):
    def __init__(self, chat_dict, *, session: 'Session'):
        super().__init__(chat_dict, session=session)
        self.title = chat_dict['chat_settings']['title']
        self.owner = chat_dict['admins'][0]
        self.admins = chat_dict['admins'][1:]
        self.member_count = chat_dict['chat_settings']['members_count']

    def __str__(self):
        return self.title

    def __repr__(self):
        return f'<Conversation "{self.title}" (id: {self.id})>'


class Message(VKObject):
    """
    Representing existing message from VK_API

    """

    def __init__(self, msg: dict, *, session: 'Session'):
        super().__init__(session=session)
        self.date: datetime.datetime = datetime.datetime.fromtimestamp(msg['date'])
        self.text: str = msg['text']
        self.sender: User = msg['sender']
        self.chat: Chat = msg['chat']
        self.conversation_message_id: int = int(msg['conversation_message_id'])

    def reply(self,
              text: str = '',
              attachments: list | None = None,
              sticker: int | None = None):
        return self._session.reply(self, text, attachments, sticker)

    def __str__(self):
        in_chat = f"{self.chat}" if isinstance(self.chat, Conversation) else ""
        return f'{self.sender}({in_chat}): {self.text}'

    def __repr__(self):
        return f'<{type(self).__name__} {str(self)}>'
