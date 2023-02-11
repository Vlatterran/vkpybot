# Quickstart

Easiest hi-bot

    from vkpybot import Bot


    bot = Bot(api_token)

    @bot.command('hi')
    def greet(message):
        return 'Hi'
    
    bot.start()
