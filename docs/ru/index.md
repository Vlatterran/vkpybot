# Быстрый старт

Самый простой приветствующий бот

    from vkpybot import Bot


    bot = Bot(api_token)

    @bot.command('Привет')
    def greet(message):
        return 'Привет'
    
    bot.start()
