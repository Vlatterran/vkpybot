import asyncio

import VK
from config import token, group_id as group, bot_admin as admin
from schedule import Schedule


def main():
    bot = VK.Bot(access_token=token, group_id=group, bot_admin_id=admin, log_file='log.log', loglevel=20)

    @bot.command('пары', use_doc=True)
    async def lectures(message: VK.Message, day: str = 'сегодня'):
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
        await message.reply(result)

    @bot.command('week', names=['неделя'])
    async def week(message: VK.Message):
        pass

    @bot.command('уведомления')
    async def notifications(message: VK.Message):
        await message.reply('Уведомления включены')
        async for text in Schedule().time_to_next_lecture():
            await message.chat.send(text)

    @bot.command(access_level=VK.AccessLevel.BOT_ADMIN)
    async def cache(message: VK.Message):
        await message.reply(bot.session.cache)

    @bot.command(access_level=VK.AccessLevel.BOT_ADMIN)
    async def logs(message: VK.Message):
        await message.reply(attachments=[await bot.session.upload_document('logs\\log.log', message.chat)])

    @bot.command()
    async def timer(message: VK.Message, delay: int = 10):
        await asyncio.sleep(delay)
        await message.reply('end')

    bot.start()


if __name__ == '__main__':
    main()
