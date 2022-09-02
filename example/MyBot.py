import VK
from schedule import Schedule


def main():
    try:
        from config import token, bot_admin as admin
    except ImportError:
        import os
        token = os.environ['token']
        admin = int(os.environ['admin'])
    bot = VK.Bot(access_token=token, bot_admin_id=admin, log_file='log.log', loglevel=20)

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
        return Schedule.lectures(day)

    @bot.command('week', names=['неделя'])
    def week(type: str = ''):
        return Schedule.week_lectures(type)

    @bot.command(access_level=VK.AccessLevel.BOT_ADMIN)
    def cache():
        return bot.session.cache

    @bot.command(access_level=VK.AccessLevel.BOT_ADMIN)
    async def logs(message: VK.Message):
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
        await Schedule.update(day, frequency, n, field, value)
        return 'Расписание обновлено'

    bot.start()


if __name__ == '__main__':
    main()
