from typing import overload, Any

from vkpybot.connection import Connection
from vkpybot.manager import MessagesManager, UsersManager

JSON = dict | list


class Session:
    _base_url: str
    _session_params: dict[str, Any]
    _connection: Connection
    messages: MessagesManager
    users: UsersManager
    _image_cache: dict

    @overload
    def __init__(self, access_token: str): ...

    @overload
    def __init__(self, access_token: str, api_version: float): ...


class GroupSession(Session):
    def __init__(self, access_token: str, api_version: float = ...) -> None: ...

    async def get_long_poll_server(self): ...

    def get_long_poll_server_row(self): ...
