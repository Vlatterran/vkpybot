import asyncio
import json
import logging
import os
from abc import ABC, abstractmethod
from typing import AsyncIterable, Dict

from aiohttp import web

from vkpybot.events import EventHandler, EventType
from vkpybot.sessions import GroupSession
from vkpybot.types import Message
from vkpybot.utils import get


class EventServer(ABC):
    def __init__(self, vk_session: GroupSession):
        self.vk_session = vk_session
        self.listeners: list[EventHandler] = []
        self.tasks: list[asyncio.Task] = []

    def create_task(self, coroutine):
        self.tasks.append(task := asyncio.create_task(coroutine))
        return task

    def bind_listener(self, listener: EventHandler):
        self.listeners.append(listener)

    async def _notify_listeners(self, event_dict):
        event, context = await self.parse_event(event_dict)
        for listener in self.listeners:
            await listener(event, **context)

    def notify_listeners(self, event_dict):
        self.create_task(self._notify_listeners(event_dict))

    async def parse_event(self, event) -> tuple[EventType, dict]:
        event_type: EventType = EventType[event['type'].upper()]
        context = {}
        match event_type:
            case EventType.MESSAGE_NEW:
                message_dict = event['object']['message']
                _wait_user = asyncio.create_task(self.vk_session.get_user(message_dict['from_id']))
                _wait_chat = asyncio.create_task(self.vk_session.get_chat(message_dict['peer_id']))
                message_dict['sender'], message_dict['chat'] = await asyncio.gather(_wait_user, _wait_chat)
                context |= {'message': Message(message_dict, session=self.vk_session),
                            'client_info': event['object']['client_info']}
            case EventType.MESSAGE_TYPING_STATE:
                context['state'] = event['object']['state']
                context['sender'] = await self.vk_session.get_user(event['object']['from_id'])
        return event_type, context

    @abstractmethod
    def listen(self):
        pass


class CallBackServer(EventServer):
    def __init__(self, vk_session: GroupSession, host='localhost', port=8080):
        super().__init__(vk_session)
        self.host = host
        self.port = port
        self.app = web.Application()

        async def hello_post(request: web.Request):
            req = await request.json()
            print(req)
            if req['type'] == 'confirmation':
                return web.Response(text=os.environ['CODE'])
            else:
                self.notify_listeners(req)
                return web.Response(text='ok')

        self.app.add_routes([web.post('/', hello_post)])

    def listen(self):
        web.run_app(self.app, host=self.host, port=self.port)
        asyncio.run(asyncio.gather(*self.tasks))


class YandexCloudFunction(EventServer):
    def __init__(self, vk_session: GroupSession):
        super().__init__(vk_session)

        async def hello_post(event: dict, context: dict):

            event = json.loads(event['body'])
            if not isinstance(event, dict):
                return
            if event['type'] == 'confirmation':
                return {'statusCode': 200,
                        'body': os.environ['CODE']
                        }
            else:
                await self._notify_listeners(event)
                return {'statusCode': 200,
                        'body': 'ok'
                        }

        self.handler = hello_post

    def listen(self):
        pass


class LongPollServer(EventServer):
    def __init__(self, vk_session: GroupSession, server: str, key: str, ts: int):
        super().__init__(vk_session)
        self.server = server
        self.key = key
        self.ts = ts

    async def check(self) -> AsyncIterable[tuple[EventType, Dict]]:
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

    def listen(self) -> None:
        asyncio.run(self._listen())

    async def _listen(self) -> None:
        try:
            while True:
                async for event in self.check():
                    self.notify_listeners(event)
        except Exception as e:
            logging.exception(e)
            await asyncio.gather(*self.tasks)

    async def __update(self):
        new = await self.vk_session.get_long_poll_server_row()
        self.server = new['server']
        self.key = new['key']
        self.ts = new['ts']
