VK is library that allows to create chatbots for vk easy and fast

# Quickstart

Easiest hi-bot

    from VK import Bot


    bot = Bot(api_token)

    @bot.command('hi')
    def greet(message):
        return 'Hi'
    
    bot.start()
