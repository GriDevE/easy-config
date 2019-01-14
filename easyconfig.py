# -------------------------------------------------------------------------------------------------------------------- #
#                                   Класс для создания и работы с конфигами
# -------------------------------------------------------------------------------------------------------------------- #
"""
                            README

* После инициализации объекта конфига можем посмотреть статус чтения файла: OK, WAR_DUPLICATE и т.д.

* Символ комментария и присваивания можно задать методом set_options().

* В написании ключей конфигов можно использовать только латинские или русские буквы, цифры и символы '_', '-'.
  Нельзя использовать символы _COMMENT, _ASSIGNED.
  Регистр в именах ключей не имеет значения при идентификации ключа, но сохраняется.

* В написании значений ключей конфигов можно использовать любые символы кроме: _COMMENT, _ASSIGNED, табуляции и
  прочих управляющих символов.
  Можно использовать сколько угодно пробелов внутри значения, пробелы и табуляция по краям значений и
  ключей игнорируются.

* Любое изменение в файле конфига: сначала создаёт файл name.tmp и записывает в него,
  после чего удаляет старый файл, потом меняет имя нового файла на оригинальное.
  В случае прерывания работы программы,
    при следующем запуске могут быть такие ситуации:
       > присутствует только name.log      - всё ок.
       > присутствует только name.tmp      - скрипт успел удалить старый name.log, только не успел переименовать
                                             name.tmp, переименовываем и всё ок, сообщаем что программа была прервана.
       > name.tmp и name.log присутствуют  - скрипт возможно не успел дописать новую версию файла name.tmp,
                                             удаляем name.tmp, сообщаем что программа была прервана.

* В конструктор передаётся путь к файлу конфига, если файл существует он загружается методом sync_file(),
  если файла нет, он создаётся при первом добавлении данных в конфиг.

                            МЕТОДЫ

sync_file()	- синхронизирует данные между объектом конфига и файлом конфига.

push(name=None, value=None, comment=None, value_refresh=True, comment_refresh=True, file_mod=True)
	Добавляет/обновляет Ключ-Значение в объекте конфига, обновляет запись в файле, если файла нет - создаёт.
    Добавляет комментарий в файл конфига, после пары 'ключ = значение', либо отдельный комментарий(не передан name),
    либо пустую строку(передан comment='').

pop(name=None, file=True) - удаляет ключ(и значение соответственно) из объекта конфига и из файла, сколько найдёт.

get_count(parameter=0) Получить колличество ключей

get_value(key) Получить значение ключа

get_keys(parameter=0) Получить список ключей.

get_index(key, keys_push_index=False) Получить индекс ключа, соответствующий порядку в котором он был расположен в файле.

create_file() - создаёт файл конфига с заменой, переносит туда все данные которые добавлены программно,
        		удаляет все ключи которые добавлены только из файла.

clear(delete_file=True) - очищает конфиг, удаляет файл.

set_options(path=None, comment=None, assigned=None, encoding=None) - переопределяет атрибуты.

                        СТАТИЧЕСКИЕ МЕТОДЫ

rename(path_in, path_out) - переименовываем файл. Возврат из функции когда убедится что переименовал.

remove(path) - удаляет файл. Возврат из функции когда убедится что удалил.

delete_key(key, keys) - удаляет указанный ключ key в списке keys, без учёта регистра; все совпадения удаляет.

"""
# -------------------------------------------------------------------------------------------------------------------- #

import os
import re


# -------------------------------------------------------------------------------------------------------------------- #

class Cfg:
    _data = {}  # dict с парами ключ:значение, ключи строчными символами.
    _keys = []  # list с ключами которые в файле,
    #             для того чтобы сохранять порядок расположения ключей в файле и регистр символов.
    _keys_push = []  # list с ключами которые мы задали методом push,
    #                  для того чтобы сохранять порядок добавления ключей методом push и регистр символов.

    remove_spaces = False  # удалять последние пустые строки при изменении файла конфига

    # Может быть OK=True либо WAR_FILE_NONE=True либо хотя бы один из оставшихся флагов(или несколько).
    # Если WAR_FILE_EMPTY=True то по любому WAR_DUPLICATE=False.
    WAR_OK = False  # успешно загружены данные из файла
    WAR_FILE_NONE = True  # файла нет
    WAR_INCORRECT_COMPLETION = False  # программа внезапно завершилась во время записи в прошлый раз
    WAR_FILE_EMPTY = False  # файл прочитан, но не найден ни один ключ
    WAR_DUPLICATE = False  # файл прочитан, были дубликаты ключей, дубликаты удалены
    WAR_SYNTAX = False  # файл прочитан, был затёрт нераспознанный текст в файле

    def __init__(self, path, comment="--", assigned="=", encoding="cp1251"):

        self._PATH = path  # путь к файлу конфига
        self._COMMENT = comment  # обозначение комментария
        self._ASSIGNED = assigned  # обозначение присваивания
        self._ENCODING = encoding  # по умолчанию "cp1251" - в Windows по умолчанию для текстовых файлов

        # Если не очистить, то в этих атрибутах остаются ссылки на объекты созданные в первом экземпляре класса
        self._data.clear()
        del self._keys[:]
        del self._keys_push[:]

        # если есть - загружаем файл конфига, если нет - ничего не делаем, создаём только когда добавят данные
        self.sync_file()

    def sync_file(self, fix_file=True, push_keys_in_file=True, sync_keys=True, sync_value=True):
        """ Синхронизирует данные между объектом конфига и файлом конфига.
        если fix_file=True  - затирает ошибки синтаксиса в файле.
        если push_keys_in_file=True  - ключи добавленные методом push, если их нет в файле - добавляет.
        если sync_keys=True  - обновляет в объекте ключи и располагает как в файле.
                           Ключи в _keys не добавленные методом push и которых нет в файле - удаляет из объекта конфига.
                           Новые ключи добавляет вместе со значением, независимо от параметра sync_value.
        если sync_value=True  - обновляет в объекте значения ключей.
        """
        self.WAR_OK = False
        self.WAR_FILE_NONE = False
        self.WAR_INCORRECT_COMPLETION = False
        self.WAR_FILE_EMPTY = False
        self.WAR_DUPLICATE = False
        self.WAR_SYNTAX = False

        # Проверяем присутствие *.tmp - значит программа некорректно завершилась в прошлый раз, во время работы с файлом
        if os.path.isfile(self._PATH + '.tmp'):

            self.WAR_INCORRECT_COMPLETION = True

            if os.path.isfile(self._PATH):
                # программа некорректно завершилась в прошлый раз,
                # скрипт возможно не успел дозаписать новую версию файла name.tmp - удаляем его
                self.remove(self._PATH + '.tmp')
            else:
                # всё норм, файл .tmp успел записаться, переименовываем его
                self.rename(self._PATH + '.tmp', self._PATH)

        # Загружаем файл
        if os.path.isfile(self._PATH):

            # читаем весь файл
            with open(self._PATH, mode='r', encoding=self._ENCODING) as f:
                lines = f.readlines()

            updated_file = False  # флаг, что файл нужно перезаписать
            keys_none = True  # флаг что не найден ни один ключ

            # удаляем пустые строки в конце, если нет в последней строке '\n' - добавляем
            if self.remove_spaces:
                updated_file = updated_file or self._delete_empty_end(lines)
            else:
                if len(lines) > 0:
                    if '\n' not in lines[-1]:
                        lines[-1] += '\n'
                        updated_file = True

            # перебираем, анализируем строки
            # затираем пробелами нераспознанный текст
            # извлекаем ключи и значения
            # новые ключи складываем в keys_name_lower, self._keys, self._keys_push, ключи и значения в self._data
            # если ключ присутствует - обновляем значение в self._data

            keys_name_lower = []  # все ключи которые найдём в файле кладём сюда в нижнем регистре
            i = 0
            while True:
                if i >= len(lines):
                    break
                line = lines[i]

                # - какие допустимые варианты могут быть:
                #   name =
                #   name = value
                #   name = //ла ла ла
                #    name= value//ла ла ла
                #    // ла ла ла
                # - сначала отделяем комментарий, тогда останутся варианты:
                #   name =
                #   name = value
                #    ла ла ла мусор
                #
                comment = ''

                # Отрезаем комментарий
                j = line.find(self._COMMENT)
                if j >= 0:
                    comment = line[j:]
                    line = line[:j]

                # Ищем ключи и значения
                #  name =
                str_re = '^[\t\v ]*([a-zA-Zа-яА-ЯёЁ0-9-_]+)[\t\v ]*' + self._ASSIGNED + '[\r\n\t\f\v ]*$'
                find_1_line = re.findall(str_re, line, flags=re.ASCII)
                #  name = value
                str_re = ('^[\t\v ]*([a-zA-Zа-яА-ЯёЁ0-9-_]+)[\r\n\t\f\v ]*' +
                          self._ASSIGNED + '[\t\v ]*([^\r\n\t\f\v]+?)[\r\n\t\f\v ]*$')
                find_2_line = re.findall(str_re, line, flags=re.ASCII)
                name = ''
                value = ''
                if (not find_1_line) and (not find_2_line):
                    # заменяем из line все символы на пробелы кроме \n
                    temp2 = len(line)
                    if '\n' in line:
                        temp2 -= 1
                    for letter in range(temp2):
                        if line[letter] != ' ':

                            self.WAR_SYNTAX = True

                            if fix_file:
                                line = line[:letter] + ' ' + line[letter + 1:]  # заменяем символ на пробел
                                updated_file = True

                elif find_1_line:
                    name = find_1_line[0]

                elif find_2_line:
                    name = find_2_line[0][0]
                    value = find_2_line[0][1]

                if name != '':

                    keys_none = False

                    name_lower = name.lower()

                    if name_lower not in keys_name_lower:

                        keys_name_lower.append(name_lower)

                        if self._data.get(name_lower) is None:
                            # появился новый ключ
                            if sync_keys:
                                self._keys.append(name)
                                self._data[name_lower] = value
                        else:
                            # обновляем значение
                            if sync_value:
                                self._data[name_lower] = value
                            # обновляем имя ключа в списках, на случай если регистр символов изменили
                            if sync_keys:
                                ind = self.get_index(name, keys_push_index=True)
                                if ind is not None:
                                    if ind[0]:
                                        self._keys_push[ind[1]] = name
                                        ind = self.get_index(name)
                                        self._keys[ind[1]] = name
                                    else:
                                        self._keys[ind[1]] = name
                    else:
                        # удаляем дублирующуюся запись
                        if fix_file:
                            if '\n' not in line:
                                line = ''
                            else:
                                line = '\n'

                            updated_file = True

                        self.WAR_DUPLICATE = True

                lines[i] = line + comment

                i += 1

            if keys_none:
                self.WAR_FILE_EMPTY = True

            # Добавляем в файл ключи из _keys_push которых нет в файле
            if push_keys_in_file:
                for k in self._keys_push:
                    if k.lower() not in keys_name_lower:
                        # Добавляем
                        if (self._data[k.lower()] is None) or (self._data[k.lower()] == ''):
                            lines.append(k + ' = \n')
                        else:
                            lines.append(k + ' = ' + self._data[k.lower()] + '\n')
                        updated_file = True

            if sync_keys:
                # Удаляем ключи из _keys которых нет в файле и в _keys_push
                keys_copy = list(self._keys)  # потому что, нельзя перебирать и изменять список одновременно
                for k in keys_copy:
                    ind = self.get_index(k)
                    if (k.lower() not in keys_name_lower) and (ind[0] is False):
                        # Удаляем ключ
                        del self._keys[ind[1]]
                        self._data.pop(k.lower())

                # Обновляем порядок расположения ключей в _keys, как в файле
                del keys_copy[:]
                for k in keys_name_lower:
                    ind = self.get_index(k)
                    if ind is not None:
                        keys_copy.append(self._keys[ind[1]])
                del self._keys[:]
                self._keys = keys_copy

            if updated_file:
                # записываем в копию сначала
                with open(self._PATH + '.tmp', mode='w', encoding=self._ENCODING) as f:
                    f.writelines(lines)
                # удаляем старый файл
                self.remove(self._PATH)
                # переименовываем копию
                self.rename(self._PATH + '.tmp', self._PATH)

        else:
            self.WAR_FILE_NONE = True
            if self.WAR_INCORRECT_COMPLETION:  # маловероятно, но это может случится
                print("error - не найден файл который только что переименовывали ", self._PATH)
                input("Нажмите Enter чтобы закрыть приложение:")
                quit()

        if not (self.WAR_FILE_NONE
                or self.WAR_INCORRECT_COMPLETION
                or self.WAR_FILE_EMPTY
                or self.WAR_DUPLICATE
                or self.WAR_SYNTAX):
            self.WAR_OK = True

    def push(self, name=None, value=None, comment=None, value_refresh=True, comment_refresh=True, file_mod=True):
        """ Добавляет/обновляет Ключ-Значение в объекте конфига, обновляет запись в файле, если файла нет - создаёт.
          Неочевидный момент!, файл когда-то считывался методом sync_file, и если от момента считывания до вызова push
          там что-то изменилось, то это не учтётся в методе push, его поведение будет основываться на
          данных в буфере(data, keys) а не в файле, и после того как он изменит ключ-значение в буфере, он попробует
          найти этот ключ в файле и обновит первый попавшийся ключ, если не найдёт - создаст новый в конце файла.
          Проверять полное сходство буфера и файла он не будет. Это контролируете вы сами используя метод sync_file().
        Добавляет комментарий в файл конфига, после пары 'ключ = значение', либо отдельный комментарий(не передан name).
          Если это отдельный комментарий(не передали ключ) - создаёт комментарий на новой строчке.
          Если это комментарий к ключу - действует в соответствии с параметром comment_refresh.

        если value_refresh=True   - создаёт новый ключ либо обновляет значение(если ключ уже есть).
        если value_refresh=False  - создаёт новый ключ либо обновляет значение(если ключ уже есть),
                                    только если у него пустое значение "".
        если comment_refresh=True   - создаёт комментарий после ключа, если уже есть - обновляет.
        если comment_refresh=False  - создаёт комментарий после ключа, если уже есть - не трогает.
        file_mod  - изменять или не изменять файл.
        """
        if name is None:
            if (comment is not None) and file_mod:

                # вставляем комментарий в файл, если файла нет - создаём
                if os.path.isfile(self._PATH):
                    # читаем весь файл
                    with open(self._PATH, mode='r', encoding=self._ENCODING) as f:
                        lines = f.readlines()
                    # добавляем комментарий в последнюю строчку
                    # если комментарий пустой - просто добавляем пустую строчку без символа комментария
                    if comment == '':
                        lines.append('\n')
                    else:
                        lines.append(self._COMMENT + comment + '\n')

                    # записываем в копию сначала
                    with open(self._PATH + '.tmp', mode='w', encoding=self._ENCODING) as f:
                        f.writelines(lines)
                    # удаляем старый файл
                    self.remove(self._PATH)
                    # переименовываем копию
                    self.rename(self._PATH + '.tmp', self._PATH)
                else:
                    # создаём файл, добавляем комментарий
                    with open(self._PATH, mode='w', encoding=self._ENCODING) as f:
                        # если комментарий пустой - просто добавляем пустую строчку без символа комментария
                        if comment.isspace() or comment == '':
                            f.writelines('\n')
                        else:
                            f.writelines(self._COMMENT + comment + '\n')
        else:
            # проверяем name и value
            if value is None:
                if self._data.get(name.lower()) is None:
                    value = ""
                else:
                    value = self._data[name.lower()]
            else:
                if self.str_isspace(value):  # если value == None или пробельные символы - вернёт True
                    value = ""

            name_ok = re.findall('^[a-zA-Zа-яА-ЯёЁ0-9-_]+$', name, flags=re.ASCII)

            if ((len(name) > 0) and name_ok
                    and (self._COMMENT not in name)
                    and (self._ASSIGNED not in name)
                    and (self._COMMENT not in value)
                    and (self._ASSIGNED not in value)):

                def update_key_in_file(key, val, comm=None):
                    """ Обновляет в файле значение ключа.
                    если ключ не найден - добавляет его в конец файла.
                    если файла нет - создаёт файл и добавляет только то, что передали в эту функцию.
                    """
                    if os.path.isfile(self._PATH):
                        # читаем весь файл
                        with open(self._PATH, mode='r', encoding=self._ENCODING) as f_2:
                            lines_2 = f_2.readlines()

                        updated_file = False
                        updated_value = False

                        # удаляем последние пустые строки, если нет в последней строке '\n' - добавляем
                        if self.remove_spaces:
                            self._delete_empty_end(lines_2)
                        # updated_file = updated_file or self._delete_empty_end(lines)
                        else:
                            if len(lines_2) > 0:
                                if '\n' not in lines_2[-1]:
                                    lines_2[-1] += '\n'
                                # updated_file = True

                        # ищем ключ в файле который совпадает с нашим, обновляем значение и комментарий
                        i2 = 0
                        while True:
                            if i2 >= len(lines_2):
                                break
                            line = lines_2[i2].lower()

                            j2 = line.find(key.lower())
                            if j2 >= 0:
                                # проверяем, нет ли до key символов кроме пробелов и '\t'
                                b = True
                                for k in range(j2):
                                    if (line[k] != ' ') and (line[k] != '\t'):
                                        b = False  # попался какой-то символ
                                        break
                                if b:
                                    # проверяем что после имени ключа
                                    jj = line.find(self._ASSIGNED)
                                    if jj >= j2 + len(key):
                                        # проверяем нет ли до '=' символов кроме пробелов и '\t'
                                        bb = True
                                        for kk in range(j2 + len(key), jj):
                                            if (line[kk] != ' ') and (line[kk] != '\t'):
                                                bb = False  # попался какой-то символ

                                        if bb:
                                            # теперь смотрим что между '=' и символом комментария
                                            jjj = line.find(self._COMMENT)
                                            if jjj >= jj + len(self._ASSIGNED):
                                                # обновляем value,
                                                # сохраняем пробелы после него и комментарий который был
                                                comment_in_file = ''
                                                for letter in range(jjj - 1, jj + len(self._ASSIGNED), -1):
                                                    temp = lines_2[i2][letter]
                                                    if (temp == ' ') or (temp == '\t') or (temp == '\v'):
                                                        comment_in_file += temp
                                                    else:
                                                        break

                                                if comment_refresh and (comm is not None):
                                                    comment_in_file = (comment_in_file[::-1] +
                                                                       self._COMMENT + comm + '\n')
                                                else:
                                                    comment_in_file = (comment_in_file[::-1] +
                                                                       lines_2[i2][jjj:])

                                                lines_2[i2] = (lines_2[i2][:j2] + key +
                                                               lines_2[i2][j2 + len(key):jj + len(self._ASSIGNED)] +
                                                               ' ' + val + comment_in_file)
                                            else:
                                                # стираем всё после '=', обновляем value, ставим comm
                                                lines_2[i2] = (lines_2[i2][:j2] + key +
                                                               lines_2[i2][j2 + len(key):jj + len(self._ASSIGNED)] +
                                                               ' ' + val)

                                                if comm is not None:
                                                    lines_2[i2] += "  " + self._COMMENT + comm

                                                lines_2[i2] += '\n'

                                            updated_value = True
                                            updated_file = True
                                            break
                            i2 += 1

                        # Если не нашли ключ в файле - добавляем ключ в конец файла
                        if updated_value is False:

                            temp_st = key + ' ' + self._ASSIGNED + ' ' + val

                            if comm is not None:
                                temp_st += "  " + self._COMMENT + comm

                            lines_2.append(temp_st + '\n')

                            updated_file = True

                        if updated_file:
                            # записываем в копию сначала
                            with open(self._PATH + '.tmp', mode='w', encoding=self._ENCODING) as f_2:
                                f_2.writelines(lines_2)
                            # удаляем старый файл
                            self.remove(self._PATH)
                            # переименовываем копию
                            self.rename(self._PATH + '.tmp', self._PATH)

                    else:
                        # файла нет - создаём файл, добавляем указанный ключ, значение и комментарий

                        lines_2 = [key + ' ' + self._ASSIGNED + ' ' + val]

                        # коммент добавляем
                        if comm is not None:
                            lines_2[0] += '  ' + self._COMMENT + comm

                        lines_2[0] += '\n'

                        # создаёт файл, если есть - заменяет
                        with open(self._PATH, mode='w', encoding=self._ENCODING) as f_2:
                            f_2.writelines(lines_2)

                def name_refresh(t_name, t_keys):
                    """ Обновляем имя ключа в списке - если найден, иначе - добавляем.
                    """
                    b = False
                    i2 = 0
                    t_name_lower = t_name.lower()
                    for n in t_keys:
                        if t_name_lower == n.lower():
                            b = True
                            t_keys[i2] = t_name
                            break
                        i2 += 1
                    if b is False:
                        t_keys.append(t_name)

                # обрезаем пробельные символы по краям значения
                value_no_spaces = value.strip(' \t\v\n\r')

                if self._data.get(name.lower()) is None:
                    # добавляем новый ключ
                    self._keys.append(name)
                    self._keys_push.append(name)  # значит этот ключ добавили методом push
                    self._data[name.lower()] = value_no_spaces

                    # обновляем этот ключ в файле и комментарий
                    if file_mod:
                        update_key_in_file(name, value, comment)

                elif self._data.get(name.lower()) != '':  # если в объекте найден ключ с не пустым значением

                    # обновляем имя ключа, чтобы регистр сохранить
                    name_refresh(name, self._keys)
                    # и в keys_push
                    name_refresh(name, self._keys_push)

                    if value_refresh:
                        self._data[name.lower()] = value_no_spaces
                        # обновляем этот ключ в файле и комментарий
                        if file_mod:
                            update_key_in_file(name, value, comment)
                    else:
                        # обновляем этот ключ в файле и комментарий, значение обновляем на всякий случай
                        if file_mod:
                            update_key_in_file(name, self._data[name.lower()], comment)

                else:  # если в объекте найден ключ с пустым '' значением

                    # обновляем имя ключа, чтобы регистр сохранить
                    name_refresh(name, self._keys)
                    # и в keys_push
                    name_refresh(name, self._keys_push)

                    self._data[name.lower()] = value_no_spaces

                    if file_mod:
                        update_key_in_file(name, value, comment)

            else:
                print("error push() - передано недопустимое имя ключа или значение: ",
                      name, ' ' + self._ASSIGNED + ' ', value)
        return

    def pop(self, name=None, file=True):
        """ Удаляет ключ(и значение соответственно) из объекта конфига и из файла, сколько найдёт.
        Если name = None
          Удаляет последнюю запись, добавленную методом push.
          Возвращает колличество оставшихся записей добавленных методом push.
        Если name = "name"
          Удаляет указанную запись, добавленную методом push или из файла.
          Возвращает колличество оставшихся записей добавленных методом push и полученных из файла.
        Если file = True
          Удалит не только в объекте но и в файле.
        """
        if name is None:

            length = len(self._keys_push)

            if length > 0:

                key = self._keys_push.pop()

                if key.lower() not in self._data:
                    raise IOError("_data не содержит всё подмножество ключей _keys, такое недопустимо," +
                                  " вы неправильно изменили данные, используйте предоставленные функции для этого.")

                self._data.pop(key.lower())

                length_0 = len(self._keys)
                length_1 = self.delete_key(key, self._keys)

                if length_0 == length_1:
                    raise IOError("_keys не содержит всё подмножество ключей _keys_push, такое недопустимо," +
                                  " вы неправильно изменили данные, используйте предоставленные функции для этого.")

                # теперь в файле
                if file:
                    self._delete_key_in_file(key)

            return len(self._keys_push)

        else:

            length_0 = len(self._keys)
            length = self.delete_key(name, self._keys)

            if length < length_0:

                self.delete_key(name, self._keys_push)

                if name.lower() not in self._data:
                    raise IOError("_data не содержит всё подмножество ключей _keys, такое недопустимо," +
                                  " вы неправильно изменили данные, используйте предоставленные функции для этого.")

                self._data.pop(name.lower())

                # теперь в файле
                if file:
                    self._delete_key_in_file(name)

            return length

    def set_options(self, path=None, comment=None, assigned=None, encoding=None):
        """ Можно переопределить атрибуты _PATH, _COMMENT, _ASSIGNED, _ENCODING.
        """
        if path is not None:
            self._PATH = path
        if comment is not None:
            self._COMMENT = comment
        if assigned is not None:
            self._ASSIGNED = assigned
        if encoding is not None:
            self._ENCODING = encoding

    def get_count(self, parameter=0):
        """ Получить колличество ключей
        parameter = 0  - вернёт общее колличество ключей.
        parameter = 1  - вернёт колличество ключей в файле, которые мы не добавляли методом push.
        parameter = 2  - вернёт колличество ключей, которые мы добавляли методом push.
        """
        if parameter == 0:
            return len(self._keys)
        elif parameter == 1:
            return len(self._keys) - len(self._keys_push)
        elif parameter == 2:
            return len(self._keys_push)
        return None

    def get_value(self, key):
        """ Получить значение ключа
        None - если ключа нет
        '' - если значения нет
        """
        value = self._data.get(key.lower())
        return value

    def get_keys(self, parameter=0):
        """ Получить список ключей.
        parameter = 0  - возвращает список всех ключей в порядке следования в файле.
        parameter = 1  - возвращает список ключей в файле, которые мы не добавляли методом push.
        parameter = 2  - возвращает список ключей, которые мы добавляли методом push.
        """
        if parameter == 0:
            return list(self._keys)
        elif parameter == 1:
            list_keys = []
            for k in self._keys:
                if k not in self._keys_push:
                    list_keys.append(k)
            return list_keys
        elif parameter == 2:
            return list(self._keys_push)
        return None

    def get_index(self, key, keys_push_index=False):
        """ Получить индекс ключа, соответствующий порядку в котором он был расположен в файле.
        если keys_push_index=True  - тогда, если в _keys_push есть ключ - будет возвращать индекс в _keys_push,
                                       соответствующий порядку в котором мы добавляли элементы.
        Возвращаемые значения:
          None - ключа нет
          кортеж (True, index) - индекс ключа(keys_push_index=True - тогда индекс в _keys_push),
                                 если он был инициализирован методом push.
          кортеж (False, index) - индекс ключа, если он был в файле(во время инициализации конфига или
                                  вызова метода sync_file), но не инициализирован методом push.
        """
        keys_lower = []
        for k in self._keys:
            keys_lower.append(k.lower())
        keys_push_lower = []
        for k in self._keys_push:
            keys_push_lower.append(k.lower())

        key = key.lower()

        if key in keys_push_lower:
            if keys_push_index:
                return True, keys_push_lower.index(key)
            else:
                return True, keys_lower.index(key)
        elif key in keys_lower:
            return False, keys_lower.index(key)
        else:
            return None

    def create_file(self):
        """ Создаёт файл конфига с заменой, переносит туда все данные которые добавлены программно,
        удаляет все ключи которые добавлены только из файла.

        если файл есть  и  данные в конфиге есть - создаёт новый файл с заменой, записывает данные
        если файл есть  и  данных в конфиге нет - удаляет файл
        если файла нет  и  данных в конфиге нет - ничего не делает, только ключи чистит
        """
        lines = self._create_list()  # удаляет ключи которые добавленны не программно

        if lines:
            # создаёт файл, если есть - заменяет
            with open(self._PATH, mode='w', encoding=self._ENCODING) as f:
                f.writelines(lines)
        else:
            if os.path.isfile(self._PATH):
                self.remove(self._PATH)

    def clear(self, delete_file=True):
        """ Очищает конфиг, удаляет файл
        """
        self._data.clear()
        # Используем del - для совместимости с python30.
        # В python v3.3 появился метод clear у списков, эквивалентный del list[:]
        del self._keys[:]
        del self._keys_push[:]
        if delete_file:
            if os.path.isfile(self._PATH):
                self.remove(self._PATH)

    # ---------------------------------------------------------------------------------------------------------------- #
    #                                               вспомогательные
    # ---------------------------------------------------------------------------------------------------------------- #

    @staticmethod
    def rename(path_in, path_out):
        """ Переименовываем файл с проверкой переименования.
        Возврат из функции когда убедится что переименовал.
        """
        try:
            if os.path.isfile(path_in):
                os.rename(path_in, path_out)
            else:
                print("error - не найден файл который нужно переименовать ", path_in)
                input("Нажмите Enter чтобы закрыть приложение:")
                quit()

            # Возвращаемся из функции когда гарантированно переименуется
            count = 0
            while not os.path.isfile(path_out):
                count += 1
                if count > 10000:
                    print("error - файл переименовывается слишком долго, либо не удаётся переименовать ", path_in,
                          " в ", os.path.basename(path_out))
                    input("Нажмите Enter чтобы продолжить:")
                    count = 0
        except OSError:
            print("error - не удалось переименовать файл ", path_in, " т.к. файл ", os.path.basename(path_out),
                  " уже существует.")
            input("Нажмите Enter чтобы закрыть приложение:")

    @staticmethod
    def remove(path):
        """ Удаляет файл с проверкой удаления.
        Возврат из функции когда убедится что удалил.
        """
        while True:
            try:
                os.remove(path)
                # Возвращаемся из функции когда гарантированно удалится
                count = 0
                while os.path.isfile(path):
                    count += 1
                    if count > 10000:
                        print("error - файл удаляется слишком долго, либо не удаётся удалить ", path)
                        input("Нажмите Enter чтобы продолжить:")
                        count = 0
                break
            except OSError:
                print("error - не удалось удалить файл, возможно указанный путь является каталогом ", path)
                input("Нажмите Enter чтобы повторить попытку:")

    @staticmethod
    def delete_key(key, keys):
        """ Удаляет указанный ключ key в списке keys, без учёта регистра; все совпадения удаляет.
        Возвращает количество оставшихся ключей.
        """
        keys_lower = []
        for k in keys:
            keys_lower.append(k.lower())

        key = key.lower()

        while key in keys_lower:
            i = keys_lower.index(key)
            del keys[i]
            del keys_lower[i]

        return len(keys)

    @staticmethod
    def _delete_empty_end(lines):
        """ Принимает список строк.
        Удаляет последние пустые строки, если нет в последней строке '\n' - добавляет
        """
        b = False

        if len(lines) > 0:
            while True:
                line = lines[-1]
                # проверяем, может эта последняя строка состоит только из пробелов или '\t', '\n'
                b = True
                for letter in line:
                    if (letter != ' ') and (letter != '\t') and (letter != '\n'):
                        b = False  # попался какой то символ
                        break
                if b:
                    # последняя строка пустая - удаляем её
                    lines.pop()
                    b = True

                    if not lines:
                        break
                else:
                    # последняя строка содержит какие-то символы
                    # добавляем '\n' если нет
                    if '\n' not in line:
                        lines[-1] += '\n'
                        b = True
                    break
        return b

    def _delete_key_in_file(self, name):
        """ Удаляет ключ в файле, все совпадения,
        не трогает комментарий.
        """
        # Удаляем ключ в файле
        if os.path.isfile(self._PATH):
            # читаем весь файл
            with open(self._PATH, mode='r', encoding=self._ENCODING) as f:
                lines = f.readlines()

            updated_file = False

            # удаляем последние пустые строки, если нет в последней строке '\n' - добавляем
            if self.remove_spaces:
                updated_file = updated_file or self._delete_empty_end(lines)
            else:
                if len(lines) > 0:
                    if '\n' not in lines[-1]:
                        lines[-1] += '\n'
                        updated_file = True

            # ищем ключ в файле который совпадает с нашим
            i = 0
            while True:
                if i >= len(lines):
                    break
                line = lines[i].lower()

                j = line.find(name.lower())
                if j >= 0:
                    # проверяем, нет ли до name символов кроме пробелов и '\t'
                    b = True
                    for k in range(j):
                        if (line[k] != ' ') and (line[k] != '\t'):
                            b = False  # попался какой то символ
                            break

                    if b:
                        # нашли предположительно совпадающий ключ, проверяем что после него
                        jj = line.find(self._ASSIGNED)
                        if jj >= j + len(name):
                            # проверяем нет ли до '=' символов кроме пробелов и '\t'
                            bb = True
                            for kk in range(j + len(name), jj):
                                if (line[kk] != ' ') and (line[kk] != '\t'):
                                    bb = False  # попался какой-то символ

                            if bb:
                                # теперь смотрим что после '=', удаляем всё до возможного символа комментария
                                jjj = line.find(self._COMMENT)
                                if jjj >= jj + len(self._ASSIGNED):
                                    # стираем всё от начала до _COMMENT
                                    lines[i] = lines[i][jjj:]
                                else:
                                    # удаляем всю строчку
                                    del lines[i]
                                    i -= 1

                                updated_file = True
                            # break - делаем чтобы все вхождения ключа удалил
                i += 1

            if updated_file:
                # записываем в копию сначала
                with open(self._PATH + '.tmp', mode='w', encoding=self._ENCODING) as f:
                    f.writelines(lines)
                # удаляем старый файл
                self.remove(self._PATH)
                # переименовываем копию
                self.rename(self._PATH + '.tmp', self._PATH)

    def _create_list(self):
        """ Возвращает список ключей, которые были созданы программно(а не из прочитанного файла),
        удаляет все ключи которые были загружены из файла.
        """
        # добавляем все записи
        lines = []
        for key in self._keys_push:
            lines.append(key + ' ' + self._ASSIGNED + ' ' + self._data[key.lower()] + '\n')

        # Очищаем _keys и _data от ключей которых нет в _keys_push
        keys_push_lower = []
        for k in self._keys_push:
            keys_push_lower.append(k.lower())

        temp_keys = []
        for k in self._keys:
            temp_keys.append(k)

        for key in temp_keys:
            if key.lower() not in keys_push_lower:
                self._keys.remove(key)
                self._data.pop(key.lower())

        if not (len(self._data) == len(self._keys) == len(self._keys_push)):
            print('error: create_file(), len(data):' + str(len(self._data)) + ' != len(keys):' +
                  str(len(self._keys)) + ' != len(keys_push):' + str(len(self._keys_push)))
            # print(self._data)
            # print(self._keys)
            # print(self._keys_push)
            quit()

        return lines

    @staticmethod
    def str_isspace(st):
        """ Проверяет, из пробельных символов ли строка
        ' ', '\t', '', None, объект не str  - вернёт True
        """
        if isinstance(st, str):
            for s in st:
                if (s != '\t') and (s != ' '):
                    return False
        return True

# -------------------------------------------------------------------------------------------------------------------- #
