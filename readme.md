VK is library that allows to create chatbots for vk easy and fast

#Quickstart
Easiest hi-bot 

    from VK import Bot


    bot = Bot(api_token)

    @bot.command('hi')
    def echo(message):
        return 'Hi'
    
    bot.start()

#Features
`Bot` - main class
###Parameters
- `access_token` - string to access api
- `bot_admin` - id of user, that will gain maximum access for bot's commands
- `session` - `GroupSession` object to access api (will be created automatically if not passed)
- `event_server` - `CallBackServer` or `LongPollServer` that will pass events to bot (LongPollServer will bew created automaticly)
- `log_file` - name of log_file (will bew created at /log directory)
- `log_level`
##Commands
`Bot.command()` - decorator for the functions that will be converted to a `Command` object

