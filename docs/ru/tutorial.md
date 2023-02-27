# Туториал

Short tutorial to create and run simple bot

## Установка

=== "pip"

    ```shell
    pip install vkpybot
    ```

=== "Poetry"

    ```shell
    poetry add vkpybot
    ```

## Импорт

```python hl_lines="1" linenums="1"
import vkpybot as vk
```

## Создание объекта бота

```python hl_lines="3 4" linenums="1"
import vkpybot as vk

token = "VK_API_TOKEN"
bot = vk.Bot(access_token=token)
```

## Добавление команды

```python hl_lines="1 9-13" linenums="1"
import asyncio

import vkpybot as vk

token = "VK_API_TOKEN"
bot = vk.Bot(access_token=token)


@bot.command
async def timer(message: vk.Message, minutes: int):
    await message.reply(f'Timer set for {minutes} minutes')
    await asyncio.sleep(minutes * 60)
    return 'Timer finished'
```

## Запуск бота

```python hl_lines="16" linenums="1"
import asyncio

import vkpybot as vk

token = "VK_API_TOKEN"
bot = vk.Bot(access_token=token)


@bot.command
async def timer(message: vk.Message, minutes: int):
    await bot.session.reply(message, f'Timer set for {minutes} minutes')
    await asyncio.sleep(minutes * 60)
    return 'Timer finished'


bot.start()
```


