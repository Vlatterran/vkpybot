import asyncio
import datetime
import re
import time

MINUTE = 60
HOUR = MINUTE * 60
DAY = HOUR * 24


class Schedule:
    schedule = {
        'понедельник': {
            'числитель': {
                'Информационная безопасность и защита информации на транспорте': {
                    'начало': '18:50',
                    'конец': '22:00',
                    'вид занятия': 'Лабораторные занятия'},
            },
            'знаменатель': {
                'Системы электронного документооборота в отраслях транспортно-дорожного комплекса': {
                    'начало': '18:50',
                    'конец': '22:00',
                    'вид занятия': 'Лабораторные занятия'},
            }
        },
        'вторник': {
            'числитель': {
                'Трудовое и предпринимательское право': {
                    'начало': '18:50',
                    'конец': '20:20',
                    'вид занятия': 'Лекции'},
                'Системы электронного документооборота в отраслях транспортно-дорожного комплекса': {
                    'начало': '22:30',
                    'конец': '20:20',
                    'вид занятия': 'Лекции'}
            },
            'знаменатель': {
                'Трудовое и предпринимательское право': {
                    'начало': '18:50',
                    'конец': '22:00',
                    'вид занятия': 'практика'},
            }
        },
        'среда': {
            'числитель': {
                'Физическая культура': {
                    'начало': '18:50',
                    'конец': '20:20',
                    'вид занятия': 'лекция'},
            },
            'знаменатель': {
                'Физическая культура': {
                    'начало': '18:50',
                    'конец': '20:20',
                    'вид занятия': 'лекция'},
            }
        },
        'четверг': {
            'числитель': {
                'Философия': {
                    'начало': '18:50',
                    'конец': '20:20',
                    'вид занятия': 'лекция'},
                'Дискретная математика': {
                    'начало': '20:20',
                    'конец': '22:00',
                    'вид занятия': 'практика'}
            },
            'знаменатель': {
                'Философия': {
                    'начало': '18:50',
                    'конец': '20:20',
                    'вид занятия': 'семинар'},
                'Дискретная математика': {
                    'начало': '20:20',
                    'конец': '22:00',
                    'вид занятия': 'практика'}
            }
        },
        'пятница': {
            'числитель': {
                'Интеграллы и диффиеренциальные уравнения ': {
                    'начало': '18:50',
                    'конец': '20:20',
                    'вид занятия': 'лекция'},
                'Иностраннный язык': {
                    'начало': '20:30',
                    'конец': '22:00',
                    'вид занятия': 'практика'}
            },
            'знаменатель': {
                'Технологии программирования': {
                    'начало': '18:50',
                    'конец': '20:20',
                    'вид занятия': 'лекция'},
                'Иностраннный язык': {
                    'начало': '20:30',
                    'конец': '22:00',
                    'вид занятия': 'практика'}
            }
        }
    }

    dec_ru = {
        0: 'понедельник',
        1: 'вторник',
        2: 'среда',
        3: 'четверг',
        4: 'пятница',
    }
    ru_dec = {
        'понедельник': 0,
        'вторник': 1,
        'среда': 2,
        'четверг': 3,
        'пятница': 4,
    }

    def show(self, days: list):
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
            is_even = 'числитель' if (times.tm_yday - 32) // 7 % 2 == 0 else 'знаменатель'
            if day in ('сегодня', '') and 0 <= times.tm_wday < 5:
                day = self.dec_ru[times.tm_wday]
                result = f'Расписание на {times.tm_mday}/{times.tm_mon}/{times.tm_year} ' \
                         f'({day}/{is_even}):'
            elif day == 'завтра' and (times.tm_wday == 6 or times.tm_wday < 4):
                if times.tm_wday == 6:
                    is_even = 'числитель' if is_even == 'знаменатель' else 'знаменатель'
                    day = 'понедельник'
                else:
                    day = self.dec_ru[times.tm_wday + 1]
                result = f'Расписание на {times.tm_mday + 1}/{times.tm_mon}/{times.tm_year} ({day}/{is_even}):'
            elif day in ('понедельник', 'вторник', 'среда', 'четверг', 'пятница'):
                if self.ru_dec[day] < times.tm_wday:
                    week = 'следующей'
                    is_even = 'числитель' if is_even == 'знаменатель' else 'знаменатель'
                else:
                    week = 'этой'
                result = f'Расписание на {day if day[-1] != "а" else day[:len(day) - 1] + "у"} {week} недели:'
            else:
                result = 'Не удалось найти расписание на указаный день'
            if result != 'Не удалось найти расписание на указаный день':
                day_sch = self.schedule[day][is_even]
                for i in day_sch:
                    result += f"\n{day_sch[i]['начало']} - {day_sch[i]['конец']}: {i} ({day_sch[i]['вид занятия']})"
            yield result

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
                is_even = 'числитель' if (times.tm_yday - 32) // 7 % 2 == 0 else 'знаменатель'
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


async def test():
    a = 1
    while True:
        yield a
        a += 1
        await asyncio.sleep(2)


async def test2():
    a = 1
    while True:
        yield a
        a += 1
        await asyncio.sleep(2)


async def main():
    async for text in test():
        print(text)


if __name__ == '__main__':
    asyncio.run(main())
