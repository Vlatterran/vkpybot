import asyncio
import datetime
import logging
import re
import time
import urllib.parse

import httpx
from bs4 import BeautifulSoup

MINUTE = 60
HOUR = MINUTE * 60
DAY = HOUR * 24


class Schedule:
    onedrive_url = 'https://1drv.ms/t/s!Aj0lqqPqhjDCgwCWwxmWAfKG-eDQ'
    location_response = httpx.get(onedrive_url)
    location_url = location_response.headers['location']
    location = httpx.get(location_url)
    query = urllib.parse.parse_qs(location.url.query)
    schedule_url = f'https://api.onedrive.com/drives/{(query[b"resid"][0].split(b"!")[0].decode())}' \
                   f'/items/{query[b"resid"][0].decode()}/content'
    schedule = httpx.get(schedule_url, params={'authkey': query[b'authkey'][0].decode()}, follow_redirects=True).json()

    dec_ru = {
        0: 'Понедельник',
        1: 'Вторник',
        2: 'Среда',
        3: 'Четверг',
        4: 'Пятница',
        5: 'Суббота',
        6: 'Воскресенье'
    }
    ru_dec = {
        'Понедельник': 0,
        'Вторник': 1,
        'Среда': 2,
        'Четверг': 3,
        'Пятница': 4,
        'Суббота': 5,
        'Воскресенье': 6
    }

    @classmethod
    def lectures(cls, day: str):
        date_regex = r'(\b(0?[1-9]|[1-2][0-9]|3[0-1])[\.\\]([1][0-2]|0?[1-9])\b)'
        if re.match(date_regex, day):
            date = [*map(int, re.split(r'[.\\-]', day))]
            requested_date = datetime.datetime(day=date[0], month=date[1], year=time.localtime().tm_year)
        else:
            requested_date = datetime.datetime.now()
            d = day.title()
            if d == '':
                pass
            if d == 'Завтра':
                requested_date += datetime.timedelta(days=1)
            elif d in cls.ru_dec:
                requested_date += datetime.timedelta(days=(cls.ru_dec[d] - requested_date.weekday()) % 7)
        try:
            requested_date = requested_date.timetuple()
            week_day = cls.dec_ru[requested_date.tm_wday]
            week_type = 'Числитель' if cls.is_week_even(requested_date) else 'Знаменатель'
            requested_schedule = cls.schedule[week_day][week_type]
            result = f'Расписание на {time.strftime("%d.%m.%Y", requested_date)} ' \
                     f'({week_day.lower()}/{week_type.lower()})'
            for i in requested_schedule:
                result += f"\n{'=' * 40}\n{i['Время занятий']}: {i['Наименование дисциплины']}\
                \n{i['Преподаватель']} | {i['Аудитория']} | {i['Вид занятий']}"
            return result
        except KeyError:
            return 'Не удалось найти расписание на указанный день'

    @staticmethod
    def is_week_even(day: time.struct_time):
        return ((day.tm_yday + datetime.datetime(day=1, month=1, year=2022).weekday()) // 7) % 2 == 1

    async def time_to_next_lecture(self):
        while True:
            times = time.localtime()
            if times.tm_wday == 6:
                print(f'waiting {DAY / 2}')
                await asyncio.sleep(DAY / 2)
            elif times.tm_wday == 5:
                await asyncio.sleep(DAY)
            elif times.tm_wday <= 4:
                day = self.dec_ru[times.tm_wday]
                now = times.tm_hour * HOUR + times.tm_min * MINUTE
                is_even = 'Числитель' if (times.tm_yday - 32) // 7 % 2 == 0 else 'Знаменатель'
                day_sch = self.schedule[day][is_even]
                for i in day_sch:
                    next_str = day_sch[i]['начало']
                    next_time = int(next_str[:2]) * HOUR + int(next_str[3:]) * MINUTE
                    if next_time > now:
                        delay = next_time - now
                        print(delay)
                        if delay <= 10 * MINUTE:
                            timer = int(delay / MINUTE)
                            yield f"{i} через {timer}"
                            await asyncio.sleep(delay + MINUTE)
                            break
                        else:
                            await asyncio.sleep(delay / 2)
                            break
                else:
                    await asyncio.sleep(DAY / 2)

    @classmethod
    async def parse(cls, group: str):
        async with httpx.AsyncClient() as client:
            soup = BeautifulSoup((await client.post('https://www.madi.ru/tplan/tasks/task3,7_fastview.php',
                                                    data={'step_no': 1, 'task_id': 7})).text)
            _groups = dict(map(lambda x: (x.attrs['value'], x.text),
                               soup.select('ul>li')))
            weekday = None
            schedule = {}
            for group_id, group_name in filter(lambda kv: kv[1].lower() == group.lower(), _groups.items()):
                response = await client.post('https://www.madi.ru/tplan/tasks/tableFiller.php',
                                             data={'tab': 7, 'gp_name': group_name, 'gp_id': group_id})
                soup = BeautifulSoup(response.text, features='lxml')
                raws = iter(soup.select('.timetable tr'))
                for raw in raws:
                    children = [*raw.findChildren(('td', 'th'))]
                    if sum(1 for _ in children) == 1:
                        try:
                            weekday = raw.text
                        except KeyError:
                            break
                        next(raws)
                    else:
                        context = {'weekday': weekday, 'group': group_name}
                        line = {}
                        for i, cell in enumerate(children):
                            match i:
                                case 0:
                                    line['Время занятий'] = cell.text
                                case 1:
                                    line['Наименование дисциплины'] = cell.text
                                case 2:
                                    line['Вид занятий'] = cell.text
                                case 3:
                                    try:
                                        context['frequency'] = cell.text
                                    except KeyError:
                                        break
                                case 4:
                                    line['Аудитория'] = cell.text
                                case 5:
                                    if cell.text == '':
                                        t = '----'
                                    else:
                                        t = cell.text
                                    line['Преподаватель'] = re.sub(r'\s{2,}', ' ', t)
                        try:
                            day = schedule.setdefault(context['weekday'], {})
                            if context['frequency'].lower() == 'еженедельно':
                                day.setdefault('Числитель', []).append(line)
                                day.setdefault('Знаменатель', []).append(line)
                            else:
                                day.setdefault(context['frequency'], []).append(line)
                        except Exception as e:
                            print(type(e), e, f'\n{context}')
                            logging.exception(e)
                            break
        cls.schedule = schedule

    @classmethod
    def week_lectures(cls, type: str):
        if type == '':
            f = 'Числитель' if cls.is_week_even(datetime.date.today().timetuple()) else 'Знаменатель'
        else:
            f = type.title()
        result = f'Расписание на {f}'
        for i in cls.ru_dec:
            try:
                requested_schedule = cls.schedule[i][f]
                result += f'\n{i}'
                for i in requested_schedule:
                    result += f"\n{'=' * 40}\n{i['Время занятий']}: {i['Наименование дисциплины']}\
                            \n{i['Преподаватель']} | {i['Аудитория']} | {i['Вид занятий']}"
            except KeyError:
                pass
        return result

    @classmethod
    async def update(cls):
        async with httpx.AsyncClient() as client:
            location_response = client.get(cls.onedrive_url)
            location_url = (await location_response).headers['location']
            location = await client.get(location_url)
            query = urllib.parse.parse_qs(location.url.query)
            schedule_url = f'https://api.onedrive.com/drives/{(query[b"resid"][0].split(b"!")[0].decode())}' \
                           f'/items/{query[b"resid"][0].decode()}/content'
            cls.schedule = (await client.get(schedule_url, params={'authkey': query[b'authkey'][0].decode()},
                                             follow_redirects=True)).json()


if __name__ == '__main__':
    asyncio.run(Schedule.parse('3ВбИТС'))
