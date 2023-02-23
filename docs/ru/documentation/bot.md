# Бот

`Bot` - основной класс

### Параметры

- `access_token: str` - токен для доступа к API ВКонтакте
- `bot_admin: int` - идентификатор пользователя с максимальными правами доступа
- `session` - `GroupSession` object to access api (will be created automatically if not passed)
- `event_server` - `CallBackServer` or `LongPollServer` that will pass events to bot (LongPollServer will bew created automatically)
- `log_file` - name of log_file (will bew created at /log directory)
- `log_level`

## Commands

`Bot.command()` - decorator for the functions that will be converted to a `Command` object

### Parameters

- `name` - the main name of command (by default the name of function)
- `aliases` - the alternative names of command
- `access_level` - the minimum [access level](#AccessLevel) of access to run command
- `message_if_deny` - string, that will be replied to message, if access_level less then `access_level`
- `use_doc` - weather or not use the documentation of function in auto-generated documentation

Commands can be declared both synchronous and asynchronous

    bot.command()
    def hi():
        return 'Hi!'

    bot.command()
    async def bye():
        return 'Bye-bye!'

You can add `message` argument to the command-function to gain access to the message, that called the command

    bot.command()
    def hi(message):
        return f'Hi, {message.sender}!'


> Framework will automatically use the returned string as text of message to reply and ignore all other returned objects (including None)

## AccessLevel

There are 3 access levels now

1. USER - every user in conversations
2. ADMIN - admins of conversation and any user in private chat with bot
3. BOT_ADMIN - user, that was declared as `bot_admin`

## Regex (Experimental)

You can write functions, that will be automatically called if message matches given pattern

    bot.regex('.*hi.*')
    async def regex_hi(message):
        await message.reply('Your message contains hi')