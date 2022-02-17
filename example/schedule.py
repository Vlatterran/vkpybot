import asyncio
import datetime
import re
import time

MINUTE = 60
HOUR = MINUTE * 60
DAY = HOUR * 24


class Schedule:
    schedule = {
        'Вторник': {
            'Знаменатель': [
                {
                    'Аудитория': '605л',
                    'Вид занятий': 'Лабораторные занятия',
                    'Время занятий': '18:50 - 20:20',
                    'Наименование дисциплины':
                        'Информационное моделирование в отраслях транспортно-дорожного комплекса',
                    'Периодичность занятий': 'Знаменатель',
                    'Преподаватель': ''
                }, {
                    'Аудитория': '605л',
                    'Вид занятий': 'Лабораторные занятия',
                    'Время занятий': '20:30 - 22:00',
                    'Наименование дисциплины':
                        'Информационное моделирование в отраслях транспортно-дорожного комплекса',
                    'Периодичность занятий': 'Знаменатель',
                    'Преподаватель': ''
                }],
            'Числитель': [
                {
                    'Аудитория': '619л',
                    'Вид занятий': 'Лабораторные занятия',
                    'Время занятий': '18:50 - 20:20',
                    'Наименование дисциплины': 'Технология разработки '
                                               'Интернет-приложений',
                    'Периодичность занятий': 'Числитель',
                    'Преподаватель': ''
                }, {
                    'Аудитория': '619л',
                    'Вид занятий': 'Лабораторные занятия',
                    'Время занятий': '20:30 - 22:00',
                    'Наименование дисциплины': 'Технология разработки Интернет-приложений',
                    'Периодичность занятий': 'Числитель',
                    'Преподаватель': ''
                }]},
        'Понедельник': {
            'Знаменатель': [
                {
                    'Аудитория': '713л',
                    'Вид занятий': 'Лекции',
                    'Время занятий': '18:50 - 20:20',
                    'Наименование дисциплины':
                        'Телекоммуникационные технологии в отраслях транспортно-дорожного комплекса',
                    'Периодичность занятий': 'Знаменатель',
                    'Преподаватель': 'Виноградов В.А.'
                }, {
                    'Аудитория': '713л',
                    'Вид занятий': 'Лекции',
                    'Время занятий': '20:30 - 22:00',
                    'Наименование дисциплины': 'Технология разработки Интернет-приложений',
                    'Периодичность занятий': 'Знаменатель',
                    'Преподаватель': 'Москалев А.Г.'
                }
            ],
            'Числитель': [
                {
                    'Аудитория': '603л',
                    'Вид занятий': 'Лекции',
                    'Время занятий': '18:50 - 20:20',
                    'Наименование дисциплины': 'Теория информации, данные, знания',
                    'Периодичность занятий': 'Числитель',
                    'Преподаватель': 'Строганов Д.В.'
                }, {
                    'Аудитория': '603л',
                    'Вид занятий': 'Лабораторные занятия',
                    'Время занятий': '20:30 - 22:00',
                    'Наименование дисциплины': 'Теория информации, данные, знания',
                    'Периодичность занятий': 'Числитель',
                    'Преподаватель': ''
                }
            ]
        },
        'Пятница': {
            'Знаменатель': [
                {
                    'Аудитория': '603л',
                    'Вид занятий': 'Лабораторные занятия',
                    'Время занятий': '18:50 - 20:20',
                    'Наименование дисциплины':
                        'Телекоммуникационные технологии в отраслях транспортно-дорожного комплекса',
                    'Периодичность занятий': 'Знаменатель',
                    'Преподаватель': ''
                }, {
                    'Аудитория': '603л',
                    'Вид занятий': 'Лабораторные занятия',
                    'Время занятий': '20:30 - 22:00',
                    'Наименование дисциплины':
                        'Телекоммуникационные технологии в отраслях транспортно-дорожного комплекса',
                    'Периодичность занятий': 'Знаменатель',
                    'Преподаватель': ''
                }
            ],
            'Числитель': [
                {
                    'Аудитория': '',
                    'Вид занятий': 'Практические занятия /семинар/',
                    'Время занятий': '18:50 - 20:20',
                    'Наименование дисциплины': 'Иностранный язык',
                    'Периодичность занятий': 'Числ. 1 раз в месяц',
                    'Преподаватель': ''
                }, {
                    'Аудитория': '',
                    'Вид занятий': 'Практические занятия /семинар/',
                    'Время занятий': '20:30 - 22:00',
                    'Наименование дисциплины': 'Иностранный язык',
                    'Периодичность занятий': 'Числ. 1 раз в месяц',
                    'Преподаватель': ''
                }
            ]
        },
        'Четверг': {
            'Знаменатель': [
                {
                    'Аудитория': 'Дистанционно',
                    'Вид занятий': 'Лекции',
                    'Время занятий': '18:50 - 20:20',
                    'Наименование дисциплины': 'Информационное моделирование в отраслях транспортно-дорожного комплекса',
                    'Периодичность занятий': 'Знаменатель',
                    'Преподаватель': 'Исмоилов М.И.'
                }, {
                    'Аудитория': 'Дистанционно',
                    'Вид занятий': 'Лекции',
                    'Время занятий': '20:30 - 22:00',
                    'Наименование дисциплины': 'Теория принятия решений',
                    'Периодичность занятий': 'Знаменатель',
                    'Преподаватель': 'Строганов В.Ю.'}],
            'Числитель': [
                {
                    'Аудитория': 'Дистанционно',
                    'Вид занятий': 'Практические занятия /семинар/',
                    'Время занятий': '18:50 - 20:20',
                    'Наименование дисциплины': 'Теория принятия решений',
                    'Периодичность занятий': 'Числитель',
                    'Преподаватель': 'Строганов В.Ю.'
                }, {
                    'Аудитория': 'Дистанционно',
                    'Вид занятий': 'Практические занятия /семинар/',
                    'Время занятий': '20:30 - 22:00',
                    'Наименование дисциплины': 'Теория принятия решений',
                    'Периодичность занятий': 'Числитель',
                    'Преподаватель': 'Строганов В.Ю.'
                }
            ]
        }
    }

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
            is_even = 'Числитель' if (times.tm_yday - 32) // 7 % 2 == 1 else 'Знаменатель'
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
            requested_time = datetime.datetime(day=date[0], month=date[1], year=time.localtime().tm_year).timetuple()
        else:
            requested_time = datetime.datetime.now()
            d = day.lower()
            if d == '':
                pass
            if d == 'завтра':
                requested_time += datetime.timedelta(days=1)
            elif d in map(str.lower, cls.ru_dec):
                pass
                if requested_time.tm_wday < cls.ru_dec[day.capitalize()]:
                    pass
            requested_time = requested_time.timetuple()
        try:
            week_day = cls.dec_ru[requested_time.tm_wday]
            week_type = 'Числитель' if cls.is_week_even(requested_time) else 'Знаменатель'
            requested_schedule = cls.schedule[week_day][week_type]
            result = f'Расписание на {time.strftime("%d.%m.%Y", requested_time)} ' \
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


if __name__ == '__main__':
    print(Schedule.lectures('Сегодня'))
