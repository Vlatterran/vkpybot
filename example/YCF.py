import vkpybot as vk
from .schedule import Schedule

import os

token = os.environ['token']
admin = int(os.environ['admin'])

session = vk.sessions.GroupSession(access_token=token)
event_server = vk.servers.YandexCloudFunction(session)

bot = vk.Bot(access_token=token, bot_admin_id=admin, loglevel=20, session=session, event_server=event_server)
print('creating bot')


@bot.command('пары', use_doc=True)
def lectures(day: str = 'сегодня'):
    """
    Отправляет расписание на указанный день
    По умолчанию используется текущая дата

    Args:
        day: день, на который будет выдано расписание
    Returns:
        None
    """
    print('пары')
    return Schedule.lectures(day)


handler = event_server.handler
