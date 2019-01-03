# Easy Config #
Если для вашей программы необходим простой конфигурационный файл, предназначенный для взаимодействия с пользователем, и вам не подходят по каким-то причинам ConfigParser и ConfigObj или не нравятся, возможно, easyconfig будет хорошим выбором.  
Также easyconfig можно использовать для логирования или для сохранения истории действий пользователя в формате txt.

## Features ##
* При каждом программном изменении конфига сначала создаётся копия, таким образом гарантируется, что файл конфига не будет повреждён. Даже при неудачном завершении во время записи ключа, при следующей инициализации конфиг-файл успешно загрузится из последней успешно сохранённой версии.
* Обозначение комментариев можно задать своё, по умолчанию "--"
* Обозначение присваивания ключу значений можно задать своё, по умолчанию "=".
* Лоялен к любым ошибкам синтаксиса в конфигурационных файлах, исправляет их (удаляет не читаемое) и сообщает о типе ошибок.
* Не поддерживает секции "[section]", конфиг просто представляет из себя строки "ключ = значение" с возможностью добавлять комментарии. 
* Все записи упорядочены, сохраняется порядок расположения как в файле, также сохраняется порядок, в котором мы их добавляли методом push.
* Значений может не быть "ключ = ", тогда при чтении значений ключа будет возвращена пустая строка "".
* В именах ключей можно использовать латинские и русские буквы, цифры и знаки "_" и "-", нельзя использовать последовательность символов, обозначающих комментарий или присваивание.
* Регистр символов в именах ключей не имеет значения при идентификации ключа, но задаётся тот, который мы установим – можно использовать это в своих целях.
* В значениях ключей можно использовать любые символы, кроме последовательностей символов комментария или присваивания, и управляющих символов. В том числе допустимо любое колличество пробелов, по краям значения пробелы обрежутся.

## Requirements ##
Python 3.0.0 и новее.

## Installation ##
Скопируйте файл easyconfig.py в папку вашего проекта.

## Usage ##
Импортируем класс.
```python
from easyconfig import Cfg
```
Инициализируем объект конфигурационного файла.
```python
config = Cfg("config.log")
```
* _если файл существует – загрузит его._  
* _если файла нет – он не будет создаваться, создаст файл только после добавления информации методом `push()`._  

Также можно установить дополнительные параметры.
```python
config = Cfg("config.log", comment = "//", assigned = ":", encoding="utf-8")
```
* _`comment` – обозначение комментария, по умолчанию `"--"`_
* _`assigned` – символ присваивания, по умолчанию `"="`_
* _`encoding` – совпадает с параметром встроенной в Python функции open()._
  _Может принимать значения:_
  * _`"utf-8"`_
  * _`"cp1251"` – используется в Easy Config по умолчанию._
  * _и прочие поддерживаемые в open()._

Статус объекта конфига после инициализации можно посмотреть так:
```python
if config.OK :
	print("OK")
elif config.WAR_FILE_NONE :
	print("WAR_FILE_NONE")
else:
	if config.WAR_INCORRECT_COMPLETION :
		print("WAR_INCORRECT_COMPLETION")
	if config.WAR_FILE_EMPTY :
		print("WAR_FILE_EMPTY")
	elif config.WAR_DUBLICATE :
		print("WAR_DUBLICATE")
	if config.WAR_SYNTAX :
		print("WAR_SYNTAX")
```
Статус обновляется после инициализации объекта конфига и после вызова функции `sync_file()`.  
`OK` – успешно загружены данные из файла.  
`WAR_FILE_NONE` – файла нет.  
`WAR_INCORRECT_COMPLETION` – программа внезапно завершилась во время записи в прошлый раз.  
`WAR_FILE_EMPTY` – файл прочитан, но не найден ни один ключ.  
`WAR_DUBLICATE` – файл прочитан, были дубликаты ключей, дубликаты удалены.  
`WAR_SYNTAX` – файл прочитан, был затёрт нераспознанный текст в файле.
## Method ##
---
```python
Cfg.sync_file(fix_file = True, push_keys_in_file = True, sync_keys = True, sync_value = True)
```
Синхронизирует объект конфига с файлом конфига.
* _если `fix_file=True` – затирает ошибки синтаксиса в файле._
* _если `push_keys_in_file=True` – ключи добавленные методом `push`, если их небыло в файле - добавляет._
* _если `sync_keys=True` – обновляет в объекте ключи и располагает как в файле._
  * _Ключи не добавленные методом `push`(которые были загружены из файла когда-то) и которых нет сейчас в файле – удаляет из объекта конфига._
  * _Новые ключи – добавляет вместе со значением, независимо от параметра `sync_value`._
* _если `sync_value=True` – обновляет в объекте значения ключей._
---
```python
Cfg.push(name=None, value=None, comment = None, value_refresh=True, comment_refresh=True, file_mod = True)
```
Добавляет новую запись ключ-значение в объект конфига(либо обновляет value, если уже есть ключ) после последней записи, обновляет в файле, если файла нет - создаёт.

> Неочевидный момент! Файл когда-то считывался методом `sync_file`, и если от момента считывания до вызова `push` там что-то изменилось, то это не учтётся в методе `push`, его поведение будет основываться на данных в объекте конфига, а не в файле, и после того как он изменит ключ-значение в объекте, он попробует найти этот ключ в файле и обновит первый попавшийся ключ, если не найдёт - создаст новый в конце файла.
Проверять полное сходство буфера и файла он не будет. Это контролируете вы сами используя метод `sync_file()`.

Добавляет комментарий в файл конфига, после пары _"ключ = значение"_, либо отдельный комментарий(если передать только `comment`). Если это отдельный комментарий(не передали ключ) - создаёт комментарий на новой строчке, иначе действует в соответствии с параметром `comment_refresh`.
* _если `value_refresh=True`  – создаёт новый ключ либо обновляет значение(если ключ уже есть)._
* _если `value_refresh=False` – создаёт новый ключ либо обновляет значение(если ключ уже есть), только если у него пустое значение `""`._
* _если `comment_refresh=True`  – создаёт комментарий после ключа, если уже есть - заменяет._
* _если `comment_refresh=False` – создаёт комментарий после ключа, если уже есть - не трогает._
* _`file_mod` – изменять или не изменять записи в файле._
---
```python
Cfg.pop(selname=None, file = True)
```
Удаляет ключ(и значение соответственно) из объекта конфига, и из файла все совпадения.
* _если `name = None`  
  – удаляет последнюю запись, добавленную методом `push`.  
  – возвращает колличество оставшихся записей добавленных методом `push`._
* _если `name = "name"`  
  – удаляет указанную запись, добавленную методом `push` или загруженную из файла.  
  – возвращает общее колличество оставшихся записей добавленных методом `push` и полученных из файла._
* _если `file = True` – удалит не только в объекте но и в файле._
---
```python
Cfg.get_count(parameter = 0)
```
Возвращает колличество ключей.
* _`parameter = 0` – вернёт общее колличество ключей._
* _`parameter = 1` – вернёт колличество ключей в файле, которые мы не добавляли методом `push`._
* _`parameter = 2` – вернёт колличество ключей, которые мы добавляли методом `push`._
---
```python
Cfg.get_value(key)
```
Возвращает значение ключа.
* _`None` – если ключа нет._
* _`''` – если значение пустое._
---
```python
Cfg.get_keys(parameter = 0)
```
Возвращает список ключей.
* _`parameter = 0` – возвращает список всех ключей, в порядке следования в файле._
* _`parameter = 1` – возвращает список ключей в файле, которые мы не добавляли методом `push`._
* _`parameter = 2` – возвращает список ключей, которые мы добавляли методом `push`._
---
```python
Cfg.get_index(key, keys_push_index = False)
```
Возвращает индекс ключа, соответствующий порядку в котором он расположен в файле.
* _если `keys_push_index=True`  - будет возвращать индекс, соответствующий порядку в котором мы добавляли ключи методом `push`, либо порядку расположения в файле если не добавляли такой ключ._

Возвращаемые значения:
* _`None` - ключа нет._
* _кортеж `(True, index)` - индекс ключа, если он был инициализирован методом `push`._
* _кортеж `(False, index)` - индекс ключа, если он был в файле(во время инициализации конфига или вызова метода `sync_file`), но не инициализирован методом `push`._
---
```python
Cfg.create_file()
```
Создаёт файл конфига с заменой, переносит туда все данные которые добавлены программно, удаляет все ключи, которые добавлены только из файла.
* _если файл есть и данные есть – создаёт файл с заменой, записывает данные._
* _если файл есть а данных нет – удаляет файл._
* _если файла нет и данных нет – ничего не делает, только ключи чистит._
---
```python
Cfg.clear(delete_file = True)
```
Очищает конфиг, удаляет файл.

---
```python
Cfg.set_options(path = None, comment = None, assigned = None, encoding = None)
```
Переопределяет атрибуты относящиеся к файлу конфига `_PATH`, `_COMMENT`, `_ASSIGNED`, `_ENCODING`.
## Examples ##
Добавляем строку с комментарием.
```python
config.push(comment="просто комментарий")
```
Добавляем ключ и значение.
```python
config.push("key", "value")
```
Можем указать комментарий, который добавится в конец строки.
```python
config.push("key", "value", "комментарий")
```
Можно добавить ключ без значения.
```python
config.push("key_1", "", comment="ключ с неустановленным значением")
```
