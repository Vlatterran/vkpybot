# Command

Чтобы добавить боту команду, используйте декоратор`@bot.command()`

```python
@bot.command()
def command():
    return "Команда выполнена"
```

## Имена и сокращения

По умолчанию название функции используется в качестве названия команды. Команду можно вызвать написав в чате `/command`

Команде можно задать кастомное имя, передав в декоратор параметр `name (str)`
Чтобы добавить более одного имени команде, надо передать параметр `names (list[str])`

> Важно: использование параметра `names` не перезаписывает имя по умолчанию. Если вы не хотите использовать название функции как одо из имён команды, вам **необходимо** указать параметр `name`


```python
#  команды с именем по умолчанию
@bot.command()
def start():
    return 'Старт'


# команда с кастомным именем
@bot.command(name='привет')
def hi():
    return 'Привет, мир!'


# команда с именем по умолчанию и дополнительными именами
@bot.command(names=['конец', 'стоп'])
def stop():
    return 'Конец'


# команда с именем по умолчанию и дополнительными именами
@bot.command(name='стоп', names=['коне'])
def stop():
    return 'Конец'
```

## Параметры

Команда может иметь параметры как обычная функция в питоне

```python
@bot.command()
def hello(name):
    return f'Hello, {name}'
```

По умолчанию все параметры будут строками (хотя бы потому что сообщение это строка)

Для указания иных типов можно использовать подсказки типов (typehints)

На данный момент поддерживаются следующие типы: `str`, `int`, `float`, `dict`

TODO: Объяснить словари


