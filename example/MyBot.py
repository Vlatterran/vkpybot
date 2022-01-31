import asyncio
import sys

import VK
from schedule import Schedule


def main():
    if len(sys.argv) == 0:
        from config import token, bot_admin as admin
    else:
        token = sys.argv[1]
        admin = int(sys.argv[2])
    bot = VK.Bot(access_token=token, bot_admin_id=admin, log_file='log.log', loglevel=20)

    @bot.command('пары', use_doc=True)
    def lectures(day: str = 'сегодня'):
        """
        Отправляет расписание на указанный день
        По умолчанию используется текущая дата

        Args:
            message: Message with command
            day: день, на который будет выдано расписание
        Returns:
            None
        """
        result = ''
        args = ['']
        if day != '':
            args[0] = day
        for text in Schedule.show(args):
            result += text + '\n\n'
        return result

    @bot.command('week', names=['неделя'])
    def week():
        pass

    @bot.command('уведомления')
    async def notifications(message: VK.Message):
        await message.reply('Уведомления включены')
        async for text in Schedule().time_to_next_lecture():
            await message.chat.send(text)

    @bot.command(access_level=VK.AccessLevel.BOT_ADMIN)
    def cache():
        return bot.session.cache

    @bot.command(access_level=VK.AccessLevel.BOT_ADMIN)
    async def logs(message: VK.Message):
        await message.reply(attachments=[await bot.session.upload_document('logs\\log.log', message.chat)])

    @bot.command()
    async def timer(delay: int = 10):
        await asyncio.sleep(delay)
        return 'end'

    bot.start()


if __name__ == '__main__':
    main()
