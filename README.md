VK is library that allows to create chatbots for vk easy and fast

![PyPI](https://github.com/Vlatterran/vkpybot/actions/workflows/publish.yaml/badge.svg)
![docs](https://github.com/Vlatterran/vkpybot/actions/workflows/docs-publish.yaml/badge.svg)
![docs](https://github.com/Vlatterran/vkpybot/actions/workflows/test.yaml/badge.svg)
![version](https://img.shields.io/pypi/v/vkpybot.svg)
![py_version](https://img.shields.io/pypi/pyversions/vkpybot.svg)

# Quickstart

Easiest hi-bot

    from VK import Bot


    bot = Bot(api_token)

    @bot.command('hi')
    def greet(message):
        return 'Hi'
    
    bot.start()
