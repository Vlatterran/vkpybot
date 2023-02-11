import vkpybot
from schedule import Schedule

schedule = Schedule(onedrive_url='https://1drv.ms/t/s!Aj0lqqPqhjDCgwCWwxmWAfKG-eDQ')


def main():
    try:
        from config import token, bot_admin as admin
    except ImportError:
        import os
        token = os.environ['token']
        admin = int(os.environ['admin'])
    bot = vkpybot.Bot(access_token=token, bot_admin_id=admin, loglevel=20)

    @bot.on_startup
    async def init_schedule():
        global schedule
        await schedule.init()
        print('schedule inited')

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
        return schedule.lectures(day)

    @bot.command('week', names=['неделя'])
    def week(week_type: str = ''):
        return schedule.week_lectures(week_type)

    @bot.command(access_level=vkpybot.bot.AccessLevel.BOT_ADMIN)
    def cache():
        return bot.session.cache

    @bot.command(access_level=vkpybot.bot.AccessLevel.BOT_ADMIN)
    async def logs(message: vkpybot.Message):
        await bot.session.reply(message, attachments=[await bot.session.upload_document('logs\\log.log', message.chat)])

    @bot.command('обновить', use_doc=True)
    async def update(day: str, frequency: str, n: int, field: str, value: str):
        """
        Команда для обновления одной записи в расписании

        Args:
            day: день недели
            frequency: Тип недели
            n: номер пары
            field: поле, которое требуется обновить
            value: новое значение поля
        """
        await schedule.update()
        return 'Расписание обновлено'

    bot.start()


if __name__ == '__main__':
    main()
