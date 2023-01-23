import logging
import time

import vkpybot
from config import token, group_id as group, bot_admin as admin

# session = vkpybot.GroupSession(token, group)
# server = vkpybot.CallBackServer(session, '192.168.10.96', '8080')

bot = vkpybot.Bot(access_token=token, group_id=group, bot_admin_id=admin,
                  log_file='debuglog.log', loglevel=logging.DEBUG)


@bot.command('test', names=['t', 'testing', 'fisting'], use_doc=True)
async def test(message: vkpybot.Message, a, b: int = 1, c: float = .1, d: str = 'D', e=1, f=.2, g=''):
    """
    Short description of command
    Args:
        message:
        a: description of a
        b: description of b
        c: description of c
        d: description of d
        e: description of e
        f: description of f
        g: description of g

    Returns:

    """
    # await message.reply(f'{a} {b} {c} {d} {e} {f} {g}')
    print(message.chat)
    await message.reply(f'Hello, {message.sender}')
    time.sleep(10)
    await message.reply(f'{message.chat}')
    # print(await bot.session.get_by_conversation_message_id(message.chat.id, message.conversation_message_id))


@bot.command('echo')
def echo():
    return 'echo'


@bot.regex('test')
async def test(message: vkpybot.Message):
    await message.reply('it works')


bot.start()
