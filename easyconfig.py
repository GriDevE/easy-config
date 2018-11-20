#----------------------------------------------------------------#
#            Класс для создания и работы с конфигами
#----------------------------------------------------------------#
# 
#                            МЕТОДЫ
# load_file()	- Загружает файл конфига(формируется структура данных data, keys), исправляет в нём обнаруженные ошибки синтаксиса(непонятные слова заменяются пробелами, дубликаты ключей удаляются по ходу чтения файла).
# 					Если у нас нет ключей которые есть в файле - ключи добавляются к нам в data и keys.
# 					Если изменились значения ключей в файле - у нас значения обновляются(даже если в файле значение удалили - у нас удаляются).
# 					Если в файле не обнаруживаются ключи которые мы назначали методом push (они хранятся в keys_push), то в файл эти ключи вносятся.
# 
# create_file()				- Создаёт файл конфига, переносит туда все данные из data и keys_push (то есть те, которые добавили методом push, а не те которые из файла загрузились)
# 								Если файл уже есть - заменяет.
# 								Очищает keys и data от ключей которых нет в keys_push.
# delete_file()									- Очищает конфиг, удаляет файл
# push(name=None, value=None, comment = None, value_refresh=True)
# 												> Создаёт новый ключ либо обновляет значение(если ключ уже есть)										- value_refresh = True
# 												> Создаёт новый ключ либо обновляет значение(если ключ уже есть), только если у него пустое значение	- value_refresh = False
# 												> Добавляет комментарий в файл конфига, после пары 'ключ = значение', либо просто(если передать только comment)
# 													Если комментарий в файле уже есть после этой записи - оставляет его.
#                                               > Обновляет ключ и значение в файле, если файла нет - создаёт и добавляет ключ и значение.
# 													Внимание неочевидная вешь!, файл когда-то считывался методом load_file, и если от момента считывания до вызова push
# 													там что-то изменилось, то это не учтётся в методе push, его поведение будет основываться на данных в буфере(data, keys) а не в файле,
# 													и после того как он изменит ключ-значение в буфере, он попробует найти этот ключ в файле и обновить его, либо создаст новый если не найдёт.
# 													Проверять полное сходство буфера и файла он не будет. Это контролируете вы сами, если файл изменяется из вне во время работы программы, на помощь методы load_file() и create_file().
# 
# pop(name=None)								- Удаляет последнюю добавленную запись методом push (в файле может и не последней быть), либо ту которую укажем, полностью, в том числе и в файле строчку целиком с комментарием
# push_list(name=None, value=None)				- ???????делаю????????Добавляет новую запись ключ-массив_значений в конфиг(либо обновляет значения если уже есть запись) после последней записи,
# 													обновляет в файле, если файла нет - создаёт???????делаю????????
# 
#----------------------------README------------------------------#
# 
# * после инициализации объекта можем посмотреть warnings: _OK, _WAR_DUBLICATE и т.д.
# 
# * Символ комментария можно задать в атрибуте _COMMENT.
# * В написании ключей конфигов можно использовать только латинские или русские буквы, цифры и символы '_' и '-' и '=' без пробелов.
#     Регистр в именах ключей не имеет значения, но сохраняется для красоты.
# * data = {}		- тут хранятся все пары ключ-значение, все ключи строчными буквами.
#   keys = [] 		- тут хранятся все ключи(с сохранением регистра символов) в порядке добавления нами, либо в порядке следования в файле.
#   keys_push = []	- тут хранятся ключи которые мы добавили методом push(с сохранением регистра символов) в порядке добавления нами.
# * В написании значений ключей конфигов можно использовать любые символы кроме: _COMMENT, '=', табуляции и прочих управляющих символов. 
#     Можно использовать сколько угодно пробелов внутри значения, пробелы и табуляция по краям значений и ключей игнорируются при считывании с файла.
#
# * Можно создавать пары ключ-значение таких типов:
#      1) ключ = значение  //комментарий
#      2) ключ =  
#         {
#         значение 1 //обязательно каждое значение с новой строчки
#         значение 2 
#         ..
#         }
# 
# * Любое изменение в файле конфига: сначала создаёт файл name.tmp и записывает в него, 
#    после чего удаляет старый файл, потом меняет имя нового файла на оригинальное.
#    В случае прерывания работы программы, 
#     при следующем запуске могут быть такие ситуации:
#        > присутствует только name.log      - всё ок
#        > присутствует только name.tmp      - скрипт успел удалить старый name.log, только не успел переименовать name.tmp, переименовываем и всё ок, сообщаем что программа была прервана
#        > name.tmp и name.log присутствуют  - скрипт возможно не успел дозаписать новую версию файла name.tmp, удаляем name.tmp, сообщаем что программа была прервана
#  
# * В конструктор передаётся путь к файлу конфига, если файл существует он загружается методом load_file(),
#    если файла нет, он создаётся при первом добавлении данных в конфиг.
#
#----------------------------------------------------------------#

import os

import re

#----------------------------------------------------------------#

class CfgCreator:

	_encoding_cfg = 'cp1251' # Используется эта кодировка, потому что она в windows(вплоть до windows 10) по умолчанию для текстовых файлов

	# ничего не возвращает, если файла нет
	_OK							= True   # всё прошло хорошо, файл загружен
	_WAR_DUBLICATE				= False  # были дубликаты записей, удалены
	_WAR_SYNTAX 				= False  # были исправлены ошибки синтаксиса в файле конфига
	_WAR_INCORRECT_COMPLETION	= False  # программа некорректно завершилась в прошлый раз


	_COMMENT = ""	# символ комментария

	_ASSIGNED = ""

	path  = ""		# путь к файлу конфига

	data = {} 	# dict, словарь с парами ключ:значение
	keys = [] 	# массив с ключами, для того чтобы сохранять порядок ключей
	keys_push = [] 	# массив с ключами которы мы определили - для того чтобы знать какие ключи создали мы, а какие загрузились из файла


	remove_spaces = True  # удалять последние пустые строки при добавлении новых записей


	def __init__(self, path, comment = "--", assigned = '=', encoding = 'cp1251'):

		self.path = path
		self._COMMENT = comment
		self._ASSIGNED = assigned
		self._encoding_cfg = encoding

		self._OK = True		
		self._WAR_DUBLICATE = False
		self._WAR_SYNTAX = False
		self._WAR_INCORRECT_COMPLETION = False

		# Если не создать новые объекты с данными то в этих атрибутах останутся ссылки на объекты созданные в первом экземпляре класса
		self.data = {}
		self.keys = []
		self.keys_push = []

		# проверяем на присутствие name.tmp - значит программа не корректно завершилась в прошлый раз во время работы с файлом 

		if os.path.isfile(path+'.tmp'):

			self._WAR_INCORRECT_COMPLETION = True
			self._OK = False

			if os.path.isfile(path):
				#программа некорректно завершилась в прошлый раз, скрипт возможно не успел дозаписать новую версию файла name.tmp - удаляем
				os.remove(path+'.tmp')
			else:
				# всё норм, файл .tmp успел записаться, переименовываем его
				os.rename(path+'.tmp', path)

			# загружаем файл конфига
			self.load_file()

		else:
			# если есть загружаем файл конфига, если нет - ничего не делаем, создаём только когда добавят данные
			if os.path.isfile(path): 
				self.load_file()


# Загружает файла конфига, проверяет корректность синтаксиса

	def load_file(self):

		if os.path.isfile(self.path):
			# читаем весь файл
			with open(self.path,  mode='r', encoding=self._encoding_cfg) as f:
				lines = f.readlines() 
			
			updated_file = False

			# удаляем последние пустые строки, если нет в последней строке '\n' - добавляем
			if self.remove_spaces:
				updated_file = updated_file or self._delete_empty_end(lines)
			else:
				if len(lines) > 0 :
					if '\n' not in lines[-1] :
						lines[-1] += '\n'
						updated_file = True
			
			# последовательно анализируем строчки
			keys_name_lower = [] # все ключи которые найдём в файле будем складывать сюда

			i = 0
			while True:
				if i >= len(lines) :
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

				# Отделяем комментарий
				j = line.find(self._COMMENT)
				if j >= 0 :
					comment = line[j:]
					line = line[:j]

				# Ищем ключи и значения
				#  name = 
				find_1_line = re.findall('^[\t\v ]*([a-zA-Zа-яА-ЯёЁ0-9_-]+)[\t\v ]*=\s*$', line, flags=re.ASCII)
				#  name = value
				find_2_line = re.findall('^[\t\v ]*([a-zA-Zа-яА-ЯёЁ0-9_-]+)\s*=[\t\v ]*([^\r\n\t\f\v=]+?)\s*$', line, flags=re.ASCII)
				if (not find_1_line) and (not find_2_line) :
					# заменяем из line все символы на пробелы кроме \n
					bb = False
					if '\n' in line :
						for letter in range( len(line) - 1 ):
							if line[letter] != ' ' :
								line = line[:letter] + ' ' + line[letter+1:] # заменяем символ на пробел
								bb = True
					else:
						for letter in range( len(line) ):
							if line[letter] != ' ' :
								line = line[:letter] + ' ' + line[letter+1:] # заменяем символ на пробел
								bb = True
					# статусы обновляем
					if bb :
						updated_file = True

						self._WAR_SYNTAX = True
						self._OK = False

				else:
					if find_1_line :
						name = find_1_line[0]

						if name.lower() not in keys_name_lower :
							keys_name_lower.append(name.lower())

							if self.data.get( name.lower() ) == None :
								# появился новый ключ
								self.keys.append(name) 
								self.data[name.lower()] = ''
							else:
								# обновляем значение
								self.data[name.lower()] = ''
						else:
							#удаляем дублирующуюся запись
							if '\n' not in line :
								line = ''
							else:
								line = '\n'

							updated_file = True

							self._WAR_DUBLICATE = True
							self._OK = False
					else:
						if find_2_line :
							name = find_2_line[0][0]
							value = find_2_line[0][1]

							if name.lower() not in keys_name_lower :
								keys_name_lower.append(name.lower())

								if self.data.get( name.lower() ) == None :
									# появился новый ключ
									self.keys.append(name) 
									self.data[name.lower()] = value
								else:
									# обновляем значение
									self.data[name.lower()] = value
							else:
								#удаляем дублирующуюся запись
								if '\n' not in line :
									line = ''
								else:
									line = '\n'	

								updated_file = True

								self._WAR_DUBLICATE = True			
								self._OK = False


				lines[i] = line + comment

				i += 1
	

			# Добавляем в файл ключи из keys_push, если их там небыло
			for k in self.keys_push :
				if k.lower() not in keys_name_lower:
					# Добавляем
					if (self.data[k.lower()] == None) or (self.data[k.lower()] == ''):
						lines.append(k+' = \n')
					else:
						lines.append(k+' = '+self.data[k.lower()] + '\n')

			if updated_file:
				# записываем в копию сначала
				with open(self.path+'.tmp',  mode='w', encoding=self._encoding_cfg) as f:
					f.writelines(lines)
				# удаляем старый файл
				os.remove(self.path)
				# переименовываем копию
				os.rename(self.path+'.tmp', self.path)

	
	# Создаёт файл конфига с заменой, переносит туда все данные которые добавлены программно, удаляет все ключи которые добавлены только из файла
	#  если файл есть и данные есть - создаёт файл с заменой, записывает данные
	#  если файл есть а данных нет - удаляет файл
	#  если файла нет и данных нет - ничего не делаем, только ключи чистим

	def create_file(self):

		lines = self._create_list()  # удаляет ключи которые добавленны не программно
		
		if lines :
			# создаёт файл, если есть - заменяет
			with open(self.path,  mode='w', encoding=self._encoding_cfg) as f:
				f.writelines(lines)
		else:
			if os.path.isfile(self.path) :
				os.remove(self.path)
				
		self._OK = True		
		self._WAR_DUBLICATE = False
		self._WAR_SYNTAX = False
		self._WAR_INCORRECT_COMPLETION = False


	# Очищает конфиг, удаляет файл

	def delete_file(self):
		self.data.clear()
		del self.keys[:]  # - для совместимости с ранними версиями python. В python v3.3 появился метод clear у списков эквивалентный del list[:]
		del self.keys_push[:]
		if os.path.isfile(self.path) :
			os.remove(self.path)
		self._OK = True		
		self._WAR_DUBLICATE = False
		self._WAR_SYNTAX = False
		self._WAR_INCORRECT_COMPLETION = False


	# Добавляет новую запись ключ-значение в конфиг(либо обновляет value если уже есть запись) после последней записи, обновляет в файле, если файла нет - создаёт

	def push(self, name=None, value=None, comment = None, value_refresh=True):

		if ((name == None) and (comment == None)) or ((name == None) and (value != None) and (comment != None)):
			return

		if (name == None) and (value == None) and (comment != None):
			# вставляем комментарий в файл, если файла нет - создаём
			if os.path.isfile(self.path):
				# читаем весь файл
				with open(self.path,  mode='r', encoding=self._encoding_cfg) as f:
					lines = f.readlines() 
				# добавляем комментарий в последнюю строчку
				if comment.isspace() or comment=='': #если комментарий пустой - просто добавляем пустую строчку без символа комментария
					lines.append('\n')
				else:
					lines.append(self._COMMENT+comment+'\n')

				# записываем в копию сначала
				with open(self.path+'.tmp',  mode='w', encoding=self._encoding_cfg) as f:
					f.writelines(lines)
				# удаляем старый файл
				os.remove(self.path)
				# переименовываем копию
				os.rename(self.path+'.tmp', self.path)
			else: 
				# создаём файл, добавляем комментарий
				with open(self.path,  mode='w', encoding=self._encoding_cfg) as f:
					if comment.isspace() or comment=='': #если комментарий пустой - просто добавляем пустую строчку без символа комментария
						f.writelines('\n')
					else:
						f.writelines(self._COMMENT+comment+'\n')
		else:

			if value == None:
				value = ''

			name_ok = re.findall('^[a-zA-Zа-яА-ЯёЁ0-9_-]+$', name, flags=re.ASCII)

			if (len(name)>0) and ( name_ok ) and (self._COMMENT not in name) and (self._ASSIGNED not in name) and (self._COMMENT not in value) and (self._ASSIGNED not in value) :

				# добавляем, name в конфиг, обновляем значение

				if self.data.get( name.lower() ) == None:
					self.keys.append(name) # появился новый ключ
					self.keys_push.append(name) # ключ который добавили мы
					self.data[name.lower()] = value
				else:
					b = False
					for n in self.keys_push:
						if name.lower() == n.lower():
							b = True
							break
					if b == False:
						self.keys_push.append(name)
				
					if value_refresh:
						self.data[name.lower()] = value
					else:
						# оставляем запись, которая была, в приоритете
						if (self.data[name.lower()] == None) or (self.data[name.lower()] == ''):
							self.data[name.lower()] = value

				# обновляем записи в файле, если файла нет - создаём
				if os.path.isfile(self.path):
					# читаем весь файл
					with open(self.path,  mode='r', encoding=self._encoding_cfg) as f:
						lines = f.readlines() 
					
					updated_file = False
					updated_value = False

					# удаляем последние пустые строки, если нет в последней строке '\n' - добавляем
					if self.remove_spaces:
						updated_file = updated_file or self._delete_empty_end(lines)
					else:
						if len(lines) > 0 :
							if '\n' not in lines[-1] :
								lines[-1] += '\n'
								updated_file = True
					
					# ищем ключ в файле который совпадает с нашим, обновляем значение и комментарий
					i = 0
					while True:
						if i >= len(lines) :
							break
						line = lines[i].lower()
						
						j = line.find( name.lower() )
						if j>=0 :
							# проверяем, нет ли до name символов кроме пробелов и '\t'
							b = True
							for k in range(j):
								if (line[k] != ' ') and (line[k] != '\t') :
									b = False # попался какой то символ
									break
							
							if b:
								# нашли предположительно совпадающий ключ, проверяем что после него
								jj = line.find(self._ASSIGNED)
								if jj >= j+len(name) :
									# проверяем нет ли до '=' символов кроме пробелов и '\t'
									bb = True
									for kk in range(j+len(name), jj):
										if (line[kk] != ' ') and (line[kk] != '\t') :
											bb = False # попался какой-то символ

									if bb:
										# теперь смотрим что после '=', удаляем всё до возможного символа комментария, подставляем value 
										jjj = line.find(self._COMMENT)
										if jjj >= jj+1 :
											# обновляем value, сохраняем пробелы после него и комментарий который был
											comment_in_file = ''
											for letter in range(jjj-1, jj+1, -1) :
												if (lines[i][letter] == ' ') or (lines[i][letter] == '\t') or (lines[i][letter] == '\v') :
													comment_in_file += lines[i][letter]
												else:
													break
											comment_in_file = comment_in_file[::-1]

											lines[i] = lines[i][:jj+1] + ' '+self.data[name.lower()] + comment_in_file+lines[i][jjj:]

										else:
											# стираем всё после '=', обновляем value
											lines[i] = lines[i][:jj+1] + ' '+self.data[name.lower()]
											# добавляем комментарий, если есть
											if (comment != None) and (comment != '') :
												lines[i] += '  '+self._COMMENT+comment
											lines[i] += '\n'											

										updated_value = True
										updated_file = True
										break
						i += 1

					# Если не обновили в файле уже стоящий ключ - не обновили потому что не нашли,
					# значит добавляем новую запись
					if updated_value == False :

						if (self.data[name.lower()] == None) or (self.data[name.lower()] == ''):
							lines.append(name+' = ')
						else:
							lines.append(name+' = '+self.data[name.lower()])

						# добавляем комментарий, если есть
						if comment != None :
							lines[-1] += '  '+self._COMMENT+comment

						lines[i] += '\n'

						updated_file = True


					if updated_file :
						# записываем в копию сначала
						with open(self.path+'.tmp',  mode='w', encoding=self._encoding_cfg) as f:
							f.writelines(lines)
						# удаляем старый файл
						os.remove(self.path)
						# переименовываем копию
						count = 0
						while os.path.isfile(self.path):
							count += 1
							if count > 1000 :
								input("Не удаётся изменить "+self.path)
								count = 0
						os.rename(self.path+'.tmp', self.path)

				else: 

					lines = self._create_list()

					# коммент добавляем
					if comment != None :
						lines[-1] = lines[-1][:len(lines[-1])-1] + '  ' + self._COMMENT + comment + '\n'

					# создаёт файл, если есть - заменяет
					with open(self.path,  mode='w', encoding=self._encoding_cfg) as f:
						f.writelines(lines)

			else:
				print('error: name in push()')
				quit()



	# Удаляет последнюю запись в конфиге, либо ту которую укажем

	def pop(self, name=None):

		if name != None :

			keys_push_lower = []
			for k in self.keys_push:
				keys_push_lower.append(k.lower())

			if name.lower() in keys_push_lower :
				self.keys_push.pop( keys_push_lower.index(name.lower()) )
				self.data.pop( name.lower() )

				keys_lower = []
				for k in self.keys:
					keys_lower.append(k.lower())

				if name.lower() in keys_lower :
					self.keys.pop( keys_lower.index(name.lower()) )


				self._delete_key_in_file(name)


		else:

			if len(self.keys) > 0 :
				key = self.keys.pop()
				self.data.pop( key.lower() )

				keys_push_lower = []
				for k in self.keys_push:
					keys_push_lower.append(k.lower())

				if key.lower() in keys_push_lower :
					self.keys_push.pop( keys_push_lower.index(key.lower()) )

				# теперь в файле

				self._delete_key_in_file(key)



	# Добавляет новую запись ключ-массив_значений в конфиг(либо обновляет значения если уже есть запись) после последней записи, обновляет в файле, если файла нет - создаёт

	# def push_list(self, name=None, value=None):
	# 	pass


#----------------------------------------------------------------#
#                        вспомогательные
#----------------------------------------------------------------#

	# удаляет последние пустые строки, если нет в последней строке '\n' - добавляет
	@staticmethod
	def _delete_empty_end(lines):

		b = False

		if len(lines) > 0 :
			while True:
				line = lines[-1]
				# проверяем, может эта последняя строка состоит только из пробелов или '\t', '\n'
				b = True
				for letter in line:
					if (letter != ' ') and (letter != '\t') and (letter != '\n') :
						b = False # попался какой то символ
						break
				if b:
					# последняя строка пустая - удаляем её
					lines.pop()
					b = True

					if len(lines) == 0 :
						break
				else:
					# последняя строка содержит какие-то символы
					# добавляем '\n' если нет
					if '\n' not in line :
						lines[-1] += '\n'
						b = True
					break

		return b


	# удаляет ключ в файле, оставляя комментарий

	def _delete_key_in_file(self, name):

		
		# Удаляем ключ в файле
		if os.path.isfile(self.path):
			# читаем весь файл
			with open(self.path,  mode='r', encoding=self._encoding_cfg) as f:
				lines = f.readlines() 
			
			updated_file = False


			# удаляем последние пустые строки, если нет в последней строке '\n' - добавляем
			if self.remove_spaces:
				updated_file = updated_file or self._delete_empty_end(lines)
			else:
				if len(lines) > 0 :
					if '\n' not in lines[-1] :
						lines[-1] += '\n'
						updated_file = True
			
			# ищем ключ в файле который совпадает с нашим
			i = 0
			while True:
				if i >= len(lines) :
					break
				line = lines[i].lower()
				
				j = line.find( name.lower() )
				if j>=0 :
					# проверяем, нет ли до name символов кроме пробелов и '\t'
					b = True
					for k in range(j):
						if (line[k] != ' ') and (line[k] != '\t') :
							b = False # попался какой то символ
							break
					
					if b:
						# нашли предположительно совпадающий ключ, проверяем что после него
						jj = line.find(self._ASSIGNED)
						if jj >= j+len(name) :
							# проверяем нет ли до '=' символов кроме пробелов и '\t'
							bb = True
							for kk in range(j+len(name), jj):
								if (line[kk] != ' ') and (line[kk] != '\t') :
									bb = False # попался какой-то символ
							
							if bb:
								# теперь смотрим что после '=', удаляем всё до возможного символа комментария
								jjj = line.find(self._COMMENT)
								if jjj >= jj+1 :
									# стираем всё от начала до _COMMENT
									lines[i] = lines[i][jjj:]
								else:
									# удаляем всю строчку
									lines.pop(i)
																			
								updated_file = True
								break
				i += 1


			if updated_file :
				# записываем в копию сначала
				with open(self.path+'.tmp',  mode='w', encoding=self._encoding_cfg) as f:
					f.writelines(lines)
				# удаляем старый файл
				os.remove(self.path)
				# переименовываем копию
				os.rename(self.path+'.tmp', self.path)


	# возвращает список ключей которые были созданы программно(а не из прочитанного файла), удаляет все ключи которые были загружены из файла

	def _create_list(self):

		# добавляем все записи
		lines = []
		for key in self.keys_push:
			lines.append(key+' = '+self.data[key.lower()]+'\n')

		# Очищаем keys и data от ключей которых нет в keys_push
		keys_push_lower = []
		for k in self.keys_push:
			keys_push_lower.append(k.lower())

		temp_keys = []
		for k in self.keys:
			temp_keys.append(k)		

		for key in temp_keys:
			if key.lower() not in keys_push_lower :
				self.keys.remove(key)
				self.data.pop( key.lower() )


		if not( len(self.data) == len(self.keys) == len(self.keys_push) ):
			print('error: create_file(), len(data):'+str(len(self.data))+' != len(keys):'+str(len(self.keys))+' != len(keys_push):'+str(len(self.keys_push)))
			# print(self.data)
			# print(self.keys)
			# print(self.keys_push)
			quit()	

		return lines


#----------------------------------------------------------------#



	# if config._OK == False:
	# 	print('config._WAR_INCORRECT_COMPLETION = '+str(config._WAR_INCORRECT_COMPLETION))	
	# 	print('config._WAR_DUBLICATE = '+str(config._WAR_DUBLICATE))
	# 	print('config._WAR_SYNTAX = '+str(config._WAR_SYNTAX))	

	# if ((config._WAR_INCORRECT_COMPLETION == True) or (config._WAR_DUBLICATE == True) or (config._WAR_SYNTAX==True)) and (config._OK == True):
	# 	print('БЯКА СО СТАТУСАМИ')
	# print('config.count  = '+str(len(config.keys)))
	