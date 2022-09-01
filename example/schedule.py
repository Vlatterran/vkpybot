import asyncio
import datetime
import json
import logging
import re
import time

import requests
from bs4 import BeautifulSoup

MINUTE = 60
HOUR = MINUTE * 60
DAY = HOUR * 24


class Schedule:
    with open('./schedule.json', 'r', encoding='utf8') as f:
        schedule = json.load(f)

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
    def show(cls, days: list):
        if days is None or len(days) == 0:
            days = ['']
        for day in days:
            date_regex = r'(\b(0?[1-9]|[1-2][0-9]|3[0-1])[\.\\]([1][0-2]|0?[1-9])\b)'
            if re.match(date_regex, day):
                date = [*map(int, re.split(r'[.\\-]', day))]
                times = datetime.datetime(day=date[0], month=date[1], year=time.localtime().tm_year).timetuple()
                day = ''
            else:
                times = time.localtime()
            is_even = 'Числитель' if (times.tm_yday - 32) // 7 % 2 == 0 else 'Знаменатель'
            if day in ('сегодня', '') and 0 <= times.tm_wday < 5:
                day = cls.dec_ru[times.tm_wday]
                result = f'Расписание на {times.tm_mday}/{times.tm_mon}/{times.tm_year} ' \
                         f'({day}/{is_even}):'
            elif day == 'завтра' and (times.tm_wday == 6 or times.tm_wday < 4):
                if times.tm_wday == 6:
                    is_even = 'Числитель' if is_even == 'Знаменатель' else 'Знаменатель'
                    day = 'Понедельник'
                else:
                    day = cls.dec_ru[times.tm_wday + 1]
                result = f'Расписание на {times.tm_mday + 1}/{times.tm_mon}/{times.tm_year} ({day}/{is_even}):'
            elif day in ('Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница'):
                if cls.ru_dec[day] < times.tm_wday:
                    week = 'следующей'
                    is_even = 'Числитель' if is_even == 'Знаменатель' else 'Знаменатель'
                else:
                    week = 'этой'
                result = f'Расписание на {day if day[-1] != "а" else day[:- 1] + "у"} {week} недели:'
            else:
                result = 'Не удалось найти расписание на указанный день'
            if result != 'Не удалось найти расписание на указанный день':
                day_sch = cls.schedule[day][is_even]
                for i in day_sch:
                    result += f"\n{'=' * 40}\n{i['Время занятий']}: {i['Наименование дисциплины']}\
                    \n{i['Преподаватель']} | {i['Аудитория']} | {i['Вид занятий']}"
            yield result

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
    def parse(cls, group: str):
        soup = BeautifulSoup(requests.post('https://www.madi.ru/tplan/tasks/task3,7_fastview.php',
                                           {'step_no': 1, 'task_id': 7}).text)
        _groups = dict(map(lambda x: (x.attrs['value'], x.text), soup.select('ul>li')))
        weekday = None
        schedule = {}
        for group_id, group_name in _groups.items():
            if group_name.lower() != group.lower():
                continue
            response = requests.post('https://www.madi.ru/tplan/tasks/tableFiller.php',
                                     {'tab': 7, 'gp_name': group_name, 'gp_id': group_id})
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
                    rooms = []
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
                                    t = '---'
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
        with open('./schedule.json', 'w', encoding='utf8') as f:
            json.dump(schedule, f, indent=4, ensure_ascii=False)
        cls.schedule = schedule


if __name__ == '__main__':
    Schedule.parse('3ВбИТС')
    print(*Schedule.show(['']))
