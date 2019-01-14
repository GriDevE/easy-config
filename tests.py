# -------------------------------------------------------------------------------------------------------------------- #
#                                       Примеры использования Easy Config
# -------------------------------------------------------------------------------------------------------------------- #

from easyconfig import Cfg


# -------------------------------------------------------------------------------------------------------------------- #

# проверка ветвлений в методе push()
def test1():
    config_2 = Cfg("test_2.log", "//", '-->')  # инициализируем

    input(1)
    config_2.push(comment="comment\t1", file_mod=False)
    # ничего не происходит, потому что file_mod = False (а комментарии сохраняются только в файле)

    input(2)
    config_2.push(comment="comment\t2")  # создастся файл с комментарием

    input(3)
    config_2.push(comment="")  # когда комментарий пустой - добавится пустая строчка

    input(4)
    config_2.push("key_1", file_mod=False)  # добавляет в объект ключ с пустым значением, в файл не добавляет
    print(config_2.get_keys(), '<' + config_2.get_value("key_1") + '>')

    input(5)
    config_2.push("key_1", "24", file_mod=False)  # устанавливает значение для ключа, в файле не обновляет
    print(config_2.get_keys(), '<' + config_2.get_value("key_1") + '>')

    input(6)
    config_2.push("key_1")  # в файл добавляет ключ, значение берёт то, которое было установленно ранее
    print(config_2.get_keys(), '<' + config_2.get_value("key_1") + '>')

    input(7)
    config_2.push("Key_1", "new value")
    # в объекте и в файле обновляет регистр символов ключа key_1, и устанавливает новое значение
    print(config_2.get_keys(), '<' + config_2.get_value("key_1") + '>')

    input(8)
    config_2.push("key_2", "")  # создаёт ключ key_2 с пустым значением
    config_2.push("key_3", "123")  # создаёт ключ key_3 со значением "123"
    print(config_2.get_keys())

    input(9)
    config_2.push("key_2", "value_2", value_refresh=False)  # устанавливает значение ключу, потому что оно было пустым
    config_2.push("key_3", "value_3", value_refresh=False)  # не установит значение, потому что оно уже установленно
    print(config_2.get_keys())

    input(10)
    config_2.push("key_2", comment="comment key_2")  # добавляет комментарий к ключу

    input(11)
    config_2.push("key_2", comment="new comment key_2", comment_refresh=False)
    # не добавляет комментарий к ключу, потому что уже есть
    config_2.push("key_1", comment="new comment key_1", comment_refresh=False)
    config_2.push("key_3", comment="new comment key_3", comment_refresh=False)
    # добавляет комментарий к ключу, потому что комментария небыло
    print(config_2.get_keys())

    input(12)
    config_2.push("key_2", comment="new comment key_2")  # добавляет комментарий к ключу, несмотря на то, что уже есть
    print(config_2.get_keys())

    input(13)
    config_2.push("a", "5", "comment a")  # добавляет ключ со значением и комментарием
    print(config_2.get_keys())

    input(14)
    config_2.pop()  # удаляет последний добавленный ключ
    print(config_2.get_keys())

    input(15)
    config_2.pop("key_1")  # удаляет ключ key_1
    print(config_2.get_keys())

    input("очистить объект конфига, удалить файлы:")
    config_2.clear()
    print(config_2.get_keys())


def test2():
    config = Cfg("config.log", "//", '-:')
    if config.WAR_OK:
        print("OK")
    elif config.WAR_FILE_NONE:
        print("FILE_NONE")
    else:
        if config.WAR_INCORRECT_COMPLETION:
            print("INCORRECT_COMPLETION")
        if config.WAR_FILE_EMPTY:
            print("FILE_EMPTY")
        elif config.WAR_DUPLICATE:
            print("DUPLICATE")
        if config.WAR_SYNTAX:
            print("SYNTAX")

    input("Создали конфиг config.log, но ключи не добавляли, соответственно файл не создался.")

    config.push(comment="комментарий")

    config.push("key", "value")

    config.push("key_1")

    config.push("key_2", "value", "комментарий 1")

    config.push("key_3", comment="комментарий 2")

    print(config.get_keys())
    input("Добавили:\n просто комментарий,\n ключ и значение,\n просто ключ без значения,"
          "\n ключ значение и комментарий,\n ключ без значения и комментарий")

    config.sync_file()

    print(config.get_keys())
    input("загрузили ещё раз")

    config.push("key", "36 %")

    input("Изменили значение ключа key.")

    config.push("key_1", "value_key_1")

    input("Добавили значение для пустого ключа key_1.")

    config.push("key_1", comment="комментарий key_1", value_refresh=False)

    input("Добавили комментарий после ключа key_1.")

    config.push("key_2", "value_key_2")

    input("Добавили значение для ключа key_2.")

    config.push("key_3", "value_key_3")

    input("Добавили значение для ключа key_3.")

    config.pop()

    input("Удаляем последний ключ.")

    config.pop("key")

    config.pop("key_2")

    input("Удаляем ключи key и key_2.")

    # --------------

    config_2 = Cfg("config_2.log", "//")

    config_2.push("key-1", "value key-1")

    config_2.push("key-2")

    config_2.push("key-3", "value key-3", "комментарий key-3")

    config_2.push("key-4", comment="комментарий key-4")

    input("Создали новый конфиг config_2.log, добавили несколько новых записей.")

    config_3 = Cfg("config_2.log", "//")

    input("Создали другой конфиг config_3, "
         "указав тот же файл config_2.log - информация из него загрузилась в config_3.")

    config_3.push("key-2", "обновили key-2", value_refresh=False)

    config_3.push("key-3", "обновили key-3", value_refresh=False)

    input("Добавили в config_3 ключи key-2 и key-3, указав параметр value_refresh=False, "
         "таким образом значения ключей которые уже были в файле определены не обновились.")

    config.clear()
    config_3.clear()
    input("Очистили конфиги, удалили файлы конфигов.")


# -----------------------------------------------------MAIN----------------------------------------------------------- #

test1()

print("\n- - -\n")

test2()
