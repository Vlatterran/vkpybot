import asyncio
import dataclasses
import json
import os
import uuid
from io import BytesIO

import aioboto3

import vkpybot as vk
import vkpybot.bot
from schedule import Schedule

TOKEN = os.environ['TOKEN']
ADMIN = int(os.environ['ADMIN'])
SCHEDULE_URL = os.environ['SCHEDULE_URL']
SCHEDULE_BUCKET = os.environ['SCHEDULE_BUCKET']
SCHEDULE_KEY = os.environ['SCHEDULE_KEY']
KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
KEY_SECRET = os.environ['AWS_SECRET_ACCESS_KEY']

S3_ENDPOINT = 'https://storage.yandexcloud.net'


@dataclasses.dataclass
class Update:
    weekday: str
    week_type: str
    n: int
    fields: dict[str, str]
    uuid: str

    @property
    def dict(self):
        return dataclasses.asdict(self)


bot = vk.Bot(access_token=TOKEN, bot_admin_id=ADMIN, loglevel=20, server_type='ycf')


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

    schedule = Schedule(SCHEDULE_URL)
    await schedule.init()
    return schedule.lectures(day)


@bot.command(names=['обновить'], use_doc=True)
async def update(weekday: str, week_type: str, lecture_n: int, fields: dict):
    """
    Добавляет изменения в расписание
    Args:
        weekday: день недели (полное название либо сокращение)
        week_type: тип недели (полностью либо сокращение)
        lecture_n: номер пары (относительный, т.е. если первой пары нет, а вторая есть, надо указать 1 вместо 2)
        fields: новые значения полей в формате имя="Сальный А.Г." (кавычки требуются в если в значение содержит пробелы)
                поля: время, имя, вид, каб, препод

    """
    res = []
    if not (weekday in Schedule.ru_dec.keys() or Schedule.shortens.get(weekday) in Schedule.ru_dec.keys()):
        res.append("Некорректный день недели")
    if not (week_type in Schedule.week_types.keys() or Schedule.shortens.get(week_type) in Schedule.week_types.keys()):
        res.append("Некорректный тип недели")

    shortens = {'время': 'Время занятий', 'имя': 'Наименование дисциплины', 'вид': 'Вид занятий', 'каб': 'Аудитория',
                'препод': 'Преподаватель'}

    err = set(fields.keys()) - set(shortens.keys()) - set(shortens.values())
    if len(err) > 0:
        res.append(f"Некорректные поля: {', '.join(fields)}")
    if len(res) > 0:
        return "\n".join(res)

    weekday = Schedule.shortens.get(weekday, weekday)
    week_type = Schedule.shortens.get(week_type, week_type)
    fields = {shortens.get(k, k): v for k, v in fields.items()}

    session = aioboto3.Session(aws_access_key_id=KEY_ID, aws_secret_access_key=KEY_SECRET)
    async with session.resource('s3', endpoint_url=S3_ENDPOINT) as s3:
        bucket = await s3.Bucket(SCHEDULE_BUCKET)
        _update = Update(n=lecture_n - 1,
                         weekday=weekday,
                         week_type=week_type,
                         fields=fields,
                         uuid=str(uuid.uuid1()))
        await bucket.put_object(Body=json.dumps(_update.dict, indent=4),
                                Key=f'upcoming/{_update.uuid}.json',
                                ContentEncoding='utf8')
    return "Ваши правки сохранены, ожидайте подтверждения"


@bot.command(names=['lsu', 'list', 'updates', 'обновления'], access_level=vk.bot.AccessLevel.ADMIN, use_doc=True)
async def list_updates():
    """
    Выводит информацию о неподтверждённых изменениях
    """
    line_template = '===={i}====\n{weekday}/{week_type}, {n}\n{update}'
    session = aioboto3.Session(aws_access_key_id=KEY_ID, aws_secret_access_key=KEY_SECRET)
    async with session.resource('s3', endpoint_url=S3_ENDPOINT) as s3:
        bucket = await s3.Bucket(SCHEDULE_BUCKET)
        updates = bucket.objects.filter(Prefix='upcoming')
        keys = [file.key async for file in updates]
        if len(keys) == 0:
            return 'No updates'
        streams = [BytesIO() for _ in range(len(keys))]
        async with asyncio.TaskGroup() as tg:
            for key, stream in zip(keys, streams):
                tg.create_task(bucket.download_fileobj(key, stream))
        message = '\n'.join(map(lambda x: line_template
                                .format(i=x.uuid,
                                        weekday=x.weekday,
                                        week_type=x.week_type,
                                        n=x.n,
                                        update=' | '.join(f'{key}={value}'
                                                          for key, value in x.fields.items())),
                                map(lambda x: Update(**json.loads(x)),
                                    map(lambda x: x.getvalue().decode(),
                                        streams))))
    return message


@bot.command(names=['принять', "одобрить", "подтвердить"], access_level=vkpybot.bot.AccessLevel.ADMIN, use_doc=True)
async def approve(update_uuid: str):
    """
    Вносит имения в основное расписание

    Args:
        update_uuid (str): uuid изменения, которое надо внести (можно узнать через команду list_updates)
    """
    buffer = BytesIO()
    key = f'upcoming/{update_uuid}.json'
    session = aioboto3.Session(aws_access_key_id=KEY_ID, aws_secret_access_key=KEY_SECRET)
    async with session.resource('s3', endpoint_url=S3_ENDPOINT) as s3:
        bucket = await s3.Bucket(SCHEDULE_BUCKET)
        await bucket.download_fileobj(key, buffer)
        _update = Update(**json.loads(buffer.getvalue()))
        buffer = BytesIO()
        await bucket.download_fileobj(SCHEDULE_KEY, buffer)
        _schedule = json.loads(buffer.getvalue())
        _schedule[_update.weekday][_update.week_type][_update.n].update(_update.fields)
        await bucket.put_object(Body=json.dumps(_schedule, indent=4).encode(),
                                Key=SCHEDULE_KEY,
                                ContentEncoding='utf8')
        async with asyncio.TaskGroup() as tg:
            copy_source = {'Bucket': bucket.name,
                           'Key': key}
            tg.create_task(bucket.copy(copy_source, f'approved/{update_uuid}.json'))
            tg.create_task((await bucket.Object(key)).delete())
    return 'Изменения внесены успешно'


@bot.command(names=['отклонить', "отказать"], access_level=vkpybot.bot.AccessLevel.ADMIN, use_doc=True)
async def reject(update_uuid: str):
    """
    Отклоняет изменения

    Args:
        update_uuid (str): uuid изменения, которое надо внести (можно узнать через команду list_updates)
    """
    key = f'upcoming/{update_uuid}.json'
    session = aioboto3.Session(aws_access_key_id=KEY_ID, aws_secret_access_key=KEY_SECRET)
    async with session.resource('s3', endpoint_url=S3_ENDPOINT) as s3:
        bucket = await s3.Bucket(SCHEDULE_BUCKET)
        async with asyncio.TaskGroup() as tg:
            copy_source = {'Bucket': bucket.name,
                           'Key': key}
            tg.create_task(bucket.copy(copy_source, f'rejected/{update_uuid}.json'))
            tg.create_task((await bucket.Object(key)).delete())
    return 'Изменения отклонены'


handler = bot.server.handler
