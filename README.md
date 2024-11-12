# task_for_candidate-v2
Расчёт изменения доли эмитентов в индексе Мосбиржи, которые торговались выше 50-дневной скользящей средней

# Подготовка к работе:
1. Создаем виртуальное окружение при помощи терминала
python -m venv venv
2. Заходим в него
./venv/Scripts/activate
3. Подгружаем библиотеки:
pip install -r requirements.txt
4. Необходимо получить собственный токен для подключения к API Тинькофф-Инвестиции, так как я свой токен убрал. Токен необходимо поместить в начале модуля processing.py в глобальную переменную (TOKEN).
5. Необходимо получить токен для бота, и создать канал для проверки работоспособности.
6. Необходимо добавить в «main.env» свои токены для API бота, для API Тинькофф-Инвестиции и тэг канала, куда будут публиковаться посты, где бот является администратором.

# Предпосылки:
1.	Все котировки собираются в единый датафрейм и с его помощью обрабатываются.
2.	Для расчёта целевого показателя бралась доля эмитентов, которые включались в базу расчёта, которая изменяется несколько раз за год.
3.	Я убрал свой API-токен для Тинькофф-Инвестиции, но оставил токен для бота и тэг группы (@teatingforbor) (неактуально для v2).
4.	Логотип для водяного знака, лист с ребалансировками базы расчёта индекса Мосбиржи и инфографика хранятся в одной директории c модулями.
5.	Модуль processing.py может работать самостоятельно без main.py.
6.	Версия Python: 3.10.7.

# Структура скрипта:
1.	config_reader.py – в нем лежат токен для подключения через API к Telegram-боту.
2.	processing.py – в данном файле содержится скрипт, который производит импорт данных через API, обработку данных и построение графика с его сохранением в текущей директории.
3.	main.py – основной файл-исполнитель, через который запускается бот, который будет отсылать инфографику в канал.
4.	database/models.py – определяет модель базы данных.
5.	env/main.env – определяет токены для бота, токен API, название канала, и параметры для подключения к базе данных, хранящейся в Docker.
6.	env/postgres.env – определяет логин, пароль и название базы данных, хранящейся в Docker.
7.	Dockerfile – файл с инструкцией для Docker для сборки образа Docker.
8.	docker-compose.yml – файл для сборки приложения, состоящего из нескольких образов Docker.

# Описание processing.py:
Функции:
1.	utcnow() – функция, возвращающая текущее время в формате UTC+0.
2.	create_df(*args) – функция, которая переводит результат запроса через API в датафрейм, с которым легко работать.
3.	cast_money(*args) – функция, возвращающая данные о цене в форму, удобную для обработки.
4.	sma_normal(*args) – функция, возвращающая скользящее среднее для стоимости ценной бумаги определённого эмитента, который торговался на протяжении года беспрерывно.
5.	sma_problem(*args) – функция, возвращающая скользящее среднее для стоимости ценной бумаги определённого эмитента, которая торговалась с перерывами или вообще перестала котироваться (сплит, обратный сплит, исключение из котировальных списков и прочее).
6.	parse_wb(*args) – функция, возвращающая два объекта: список эмитентов, которые входили в состав индекса Мосбиржи за последний год, и список кортежей: первый элемент кортежа – датафрейм (из одного столбца) с составом индекса в определенный промежуток времени, второй элемент – словарь с началом и концом этого промежутка.
7.	import_candles(*args) – функция, возвращающая котировки ценных бумаг. Через класс Client при помощи т.н. службы (из документации) instruments и метода share_by находим идентификатор figi по тикеру инструмента. Далее по figi Через класс Client при помощи т.н. службы (из документации) market_data и метода get_candles импортируем котировки ценной бумаги, которую потом оборачиваем в датафрейм, далее в ходе цикла объединяем все котировки в единый датафрейм, который является выходом функции. Данные импортируются более чем за год, чтобы скользящее среднее корректно рассчиталось.
8.	make_pic() – функция, в которой происходят импорт котировок через API, вычисления и вывод графика, в которой используются вышеуказанные функции. Итог работы – сохранение графика с динамикой доли эмитентов в индексе Мосбиржи, торгующихся выше 50-дневной скользящей средней и динамикой самого индекса Мосбиржи с добавлением водяного знака и логотипа, а также передает дату последнего рассчитанного значения и само рассчитанное значение.

На сайте Московской биржи лежат данные о ребалансировке базы расчёта индекса, которая изменяется каждую третью пятницу марта, июня, сентября и декабря, то есть в конце каждого квартала. Необходимо загрузить информацию о ребалансировках с сайта Мосбиржи перед началом работы.

# Рассмотрим подробнее make_pic():
1.	Определяем список эмитентов (unique_code_list), чьи ЦБ были в индексе Мосбиржи за последний год и список кортежей (new_list_imoex).
2.	Создаем пустой датафрейм (df_quotes).
3.	При помощи цикла заполняем df_quotes котировками ЦБ эмитентов из unique_code_list.
4.	Запрашиваем через API котировки индекса Мосбиржи.
5.	Определяем эмитентов, которые торговались всегда на протяжении года (normal_columns) и тех, чьи ЦБ торговались с перерывами (problem_columns).
6.	Рассчитываем скользящее среднее для эмитентов двух видов, описанных в предыдущем пункте.
7.	При помощи цикла проходимся по каждому периоду времени, в каждом из которых была своя база расчёта индекса Мосбиржи, рассчитываем долю тех эмитентов, которые торговались выше 50-дневной скользящей средней, после чего столбцы с днями торговых сессий и целевым показателем помещаем в итоговый датафрейм (df_result).
8.	Актуализируем итоговый датафрейм.
9.	Создаем и выгружаем график в текущую директорию, где лежит скрипт.
10.	Возвращаем последнюю дату расчёта и рассчитанную долю акций эмитентов в IMOEX, торгующихся выше 50-дневной скользящей средней.

# Описание main.py:

Необходимо создать своего бота через BotFather в Telegram, дать ему имя и получить токен доступа.
Также необходимо создать канал в Telegram, добавить бота в канал, как администратора.

1.	Получаем инфографику через функцию make_pic() из модуля processing.py.
2.	Создаём асинхронную функцию send_gragh(), которая инициализирует бота, передав ему токен. После чего при помощи метода send_media_group, передав ей идентификатор группы и наш график. Отсылаем инфографику в канал.
3.	Создаём асинхронную функцию main(), которая запускает send_gragh().
4.	Происходит проверка, чтобы скрипт запускался из модуля main.py.
5.	При помощи AsyncIOScheduler задаём интервалы работы скрипта (каждый день недели в 12 часов утра по системному времени).
6.	Запускаем поток событий.

# База данных:
Схема данных:
1.	id – первичный ключ (целое, индексируемое),
2.	time – дата поста (строковое),
3.	post_text – текст публикации (строковое),
4.	value_share – процент акций в IMOEX, торгующихся выше 50-дневной скользящей средней (вещественное).

# Принцип работы:
1.	Создаем модель (таблица Notifications),
2.	Инициализируем движок БД (при помощи ссылки, которая генерируется в config_reader.py на основе данных из main.env),
3.	Создаём асинхронную сессию,
4.	Создаем функцию add_column(*args), которая добавляет в столбцы таблицы данные, полученные на выходе функции make_pic(*args), а также при помощи динамически изменяющейся строки.
5.	Создаем функцию init_models(), которая создает таблицы внутри базы на основе моделей.

# Docker:
Для работы с Docker был установлен WSL (терминал Linux).
При помощи Dockerfile формируем образ. При помощи docker-compose.yml формируем приложение на основе нескольких образов Docker (сам скрипт, PostgreSQL, pgAdmin). Для запуска сборки контейнеров на основе нескольких образов Docker необходимо ввести команду в терминале WSL (со всеми операциями с Docker необходимо запустить Docker desktop):
docker compose up
Контейнер внутри приложения будет называться postgres_main (указано в docker-compose.yml). Чтобы зайти в базу данных необходимо ввести следующие команды поочередно:
docker compose exec postgres_main bash
psql -U postgres
\c notdb
select * from notifications;

# Изменения в v2:
1.	Исправлена неточность, когда для постинга графика, данные не пересчитывались, то есть отсылался один раз рассчитанный график много раз.
2.	Все конфиденциальные ключи и прочее были добавлены в отдельный файл «.env».
3.	Скрипт был помещен в Docker и подключена база данных.
4.	Добавлена динамически изменяющаяся подпись к публикуемому графику.
