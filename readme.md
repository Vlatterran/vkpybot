VK is library that allows to create chatbots for vk easy and fast

#Quickstart
Easiest hi-bot 

    from VK import Bot


    bot = Bot(api_token, group_id)

    @bot.command('hi')
    def echo(message):
        return 'Hi'
    
    bot.start()
