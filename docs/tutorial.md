# Tutorial

Short tutorial to create and run simple bot

## Installation

```shell
pip install vkpybot
```

## Importing

```python hl_lines="1" linenums="1"
import vkpybot as vk
```

## Creating bot instance

```python hl_lines="3 4" linenums="1"
import vkpybot as vk

token = "VK_API_TOKEN"
bot = vk.Bot(access_token=token)
```

## Adding command

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

## Starting bot

```python hl_lines="15" linenums="1"
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


