#----------------------------------------------------------------#
#                Примеры использования Easy Config
#----------------------------------------------------------------#

from easyconfig import CfgCreator

#----------------------------------------------------------------#

if "\n" == None :
	print("равен")


config = CfgCreator("config.log", "//")

# input("Создали конфиг config.log, но ключи не добавляли, соответственно файл не создался.")


config.push(comment="комментарий")

config.push("key", "value")

config.push("key_1")

config.push("key_2", "value", "комментарий 1")

config.push("key_3", comment="комментарий 2")

input("Добавили:\n просто комментарий,\n ключ и значение,\n просто ключ без значения,\n ключ значение и комментарий,\n ключ без значения и комментарий")


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

config_2 = CfgCreator("config_2.log", "//")

config_2.push("key-1", "value key-1")

config_2.push("key-2")

config_2.push("key-3", "value key-3", "комментарий key-3")

config_2.push("key-4", comment="комментарий key-4")

input("Создали новый конфиг config_2.log, добавили несколько новых записей.")


config_3 = CfgCreator("config_2.log", "//")

input("Создали другой объект конфига config_3, указав тот же файл config_2.log - информация из него загрузилась в config_3.")

config_3.push("key-2", "обновили key-2", value_refresh=False)

config_3.push("key-3", "обновили key-3", value_refresh=False)

input("Добавили в config_3 ключи key-2 и key-3, указав параметр value_refresh=False, таким образом значения ключей которые уже были в файле определены не обновились.")


config.delete_file()
config_3.delete_file()
input("Удалили конфиги файлы конфигов.")