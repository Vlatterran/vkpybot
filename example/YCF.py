import io
import json
import os
import uuid

import vkpybot as vk

import aioboto3
from vkpybot import Message

from schedule import Schedule

token = os.environ['TOKEN']
admin = int(os.environ['ADMIN'])
schedule_url = os.environ['SCHEDULE_URL']

bot = vk.Bot(access_token=token, bot_admin_id=admin, loglevel=20, server_type='ycf')


@bot.command('обновить')
async def update(message: Message, week_day: str, week_type: str, lecture_n: int, fields: dict):
    res = []
    if week_day not in Schedule.ru_dec.keys():
        res.append("Некорректный день недели")
    if week_type not in Schedule.shortens.values():
        res.append("Некорректный тип недели")

    err = set(fields.keys()) - {'Время занятий', 'Наименование дисциплины', 'Вид занятий', 'Аудитория', 'Преподаватель'}
    if len(err) > 0:
        res.append(f"Некорректные поля: {', '.join(fields)}")
    if len(res) > 0:
        return "\n".join(res)

    schedule_key = os.environ['SCHEDULE_KEY']
    key_id = os.environ['AWS_ACCESS_KEY_ID']
    key_secret = os.environ['AWS_SECRET_ACCESS_KEY']

    session = aioboto3.Session(aws_access_key_id=key_id, aws_secret_access_key=key_secret)
    async with session.resource('s3', endpoint_url='https://storage.yandexcloud.net') as s3:
        bucket = await s3.Bucket('schedule')
        update_record = {'n': lecture_n,
                         'week_day': week_day,
                         'week_type': week_type,
                         'update': fields}

        await bucket.upload_fileobj(io.StringIO(json.dumps(update_record)),
                                    f'{message.sender.id}_{uuid.uuid1()}_{schedule_key}')
    return "Ваши правки сохранены, ожидайте одобрения"


@bot.command('пары', use_doc=True)
async def lectures(day: str = 'сегодня'):
    """
    Отправляет расписание на указанный день
    По умолчанию используется текущая дата

    Args:
        day: день, на который будет выдано расписание
    Returns:
        None
    """

    schedule = Schedule(schedule_url)
    await schedule.init()
    return schedule.lectures(day)


handler = bot.server.handler
