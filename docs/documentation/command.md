# Command

To add commands to your bor use `@bot.command()` decorator

```python
@bot.command()
def command():
    return "Command executed"
```

## Name and aliases

By default, the name of function will be used as name of command, so you can call it by writing `/command` in chat

You can specify custom name for command by providing `name (str)` parameter to decorator
To add more than one name for command, provide `names (list[str])` parameter

> Note: using `names` doesn't rewriting default name, so if you don't want to use function's name as command's name, you
**must** provide name

```python
# command with default name
@bot.command()
def start():
    return 'starting'


# command with custom name
@bot.command(name='hello')
def hi():
    return 'Hello, world!'


# command with default name and aliases
@bot.command(names=['end', 'break'])
def stop():
    return 'Ending'


# command with default custom and aliases
@bot.command(name='break', names=['end', 'break'])
def stop():
    return 'Ending'
```

## Parameters

Command can have parameters as normal python functions

```python
@bot.command()
def hello(name):
    return f'Hello, {name}'
```

By default, all parameters will be a string (at least because message consists of strings)

You can use typehint to automatically convert parameters to other types

Currently supported: `str`, `int`, `float`, `dict`

TODO: explain dict


