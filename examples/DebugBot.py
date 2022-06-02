import logging
import time
import yaml
import pathlib
import core.VK as VK

def main():
    config_file = 'config.yaml'
    with open(config_file, 'r') as file:
        config= yaml.safe_load(file)
        print(config)
    token=config["token"]
    log_path=config["log_path"]
    admin=config["bot_admin"]

    if not pathlib.Path(log_path).exists():
        pathlib.Path(log_path).mkdir()

    # setting path
    
    # from VK import VK
    # importing

    # session = VK.GroupSession(token, group)
    # server = VK.CallBackServer(session, '192.168.10.96', '8080')

    bot = VK.Bot(access_token=token, bot_admin_id=admin,
                log_file=f'{log_path}/debuglog.log', loglevel=logging.DEBUG)


    @bot.command('test', names=['t', 'testing', 'fisting'], use_doc=True)
    async def test(message: VK.Message, a, b: int = 1, c: float = .1, d: str = 'D', e=1, f=.2, g=''):
        """
        Short description of command
        Args:
            message:
            a: description of a
            b: description of b
            c: description of c
            d: description of d
            e: description of e
            f: description of f
            g: description of g

        Returns:

        """
        # await message.reply(f'{a} {b} {c} {d} {e} {f} {g}')
        print(message.chat)
        await message.reply(f'Hello, {message.sender}')
        time.sleep(10)
        await message.reply(f'{message.chat}')
        # print(await bot.session.get_by_conversation_message_id(message.chat.id, message.conversation_message_id))


    @bot.command('echo')
    def echo():
        return 'echo'


    @bot.regex('test')
    async def test(message: VK.Message):
        await message.reply('it works')


    bot.start()

if __name__ =="__main__":
    main()