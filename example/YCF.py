import vkpybot as vk
from schedule import Schedule


import os

token = os.environ['token']
admin = int(os.environ['admin'])

bot = vk.Bot(access_token=token, bot_admin_id=admin, loglevel=20, server_type='ycf')


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
    schedule = Schedule(onedrive_url='https://1drv.ms/t/s!Aj0lqqPqhjDCgwCWwxmWAfKG-eDQ')
    await schedule.init()
    return schedule.lectures(day)
