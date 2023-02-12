import datetime
import json
import re

import pytest
import requests_mock
from aioresponses import aioresponses

import vkpybot


def api_method(method):
    return re.compile(rf'https://api.vk.com/method/{method}.*')


def test_api_method():
    assert api_method('users.get').match('https://api.vk.com/method/users.get')
    assert api_method('users.get').match('https://api.vk.com/method/users.get?user_id=1')


@pytest.fixture(scope='module')
def mock():
    with requests_mock.Mocker() as m:
        yield m


@pytest.fixture(scope='module')
def aio_mock():
    with aioresponses() as m:
        m.get(api_method('messages.send'), payload={'response': 'ok'})
        m.get(api_method('users.get'),
              payload={'response': [
                  {'id': 1,
                   'first_name': 'Vlaterran',
                   'last_name': 'Vlatterran',
                   'is_closed': True,
                   'can_access_closed': False,
                   }]})
        m.get(api_method('messages.getConversationsById'),
              payload={
                  'response': {
                      'items': [
                          {
                              'peer': {
                                  'type': 'chat',
                                  'id': 1,
                              },
                              'chat_settings': {
                                  'owner_id': 1,
                                  'admin_ids': [1],
                                  'title': 'test',
                                  'members_count': 0,
                              }
                          }
                      ]
                  }
              })
        yield m


@pytest.fixture(scope='module')
def bot(mock) -> vkpybot.Bot:
    mock.get(api_method('groups.getById'), json={'response': [{'id': 123456789, 'name': 'test'}]})
    return vkpybot.Bot(access_token='token', server_type='ycf')


@pytest.mark.dependency(name='sync_command')
def test_crete_sync_command(bot: vkpybot.Bot):
    @bot.command()
    def hi():
        return 'Hi'


@pytest.mark.dependency(name='async_command')
def test_crete_async_command(bot: vkpybot.Bot):
    @bot.command()
    async def async_hi():
        return 'Hi'


@pytest.mark.dependency(depends=['async_command'])
@pytest.mark.asyncio
async def test_handle(bot: vkpybot.Bot, aio_mock):
    message_event = {
        'type': 'message_new',
        'object': {
            'message': {
                'text': '/async_hi',
                'from_id': 1,
                'peer_id': 1,
                'date': datetime.datetime.now().timestamp(),
                'conversation_message_id': 1,
            },
            'client_info': {}
        }
    }
    await bot.server.handler({'body': json.dumps(message_event)}, {})
    aio_mock.requests.get()

