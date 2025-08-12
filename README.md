Провеьте чтобы устройство с клиентом, сервером и сервис были подключены к одной локальной сети
----Запуск сервера(backend)----
Для работы необходимо установить PostgreSQL
В psql создаем Базу данных и пользователя, пример: createdb bezna createuser --interactive psql -c "ALTER USER bezna WITH PASSWORD '12345678';" psql -c "GRANT ALL PRIVILEGES ON DATABASE bezna TO bezna;"
В случае изменения названий баззы данных, меняйте название в Celsya/backend/RAI_bezna/setting.py в поле DATABASES на свои
В файле Celsya/backend/roadmap/microservice.py измените ROADMAP_API_URL на ссылку открытого порта устройства с сервисом
Переходим в папку проекта и создаем виртуальное окружение python: python -m venv backend_venv
Cкачиваем зависимости: pip install -r requirements.txt
Переходим в backend: cd .\backend
Запускаем миграцию данных: python manage.py makemigrations roadmap
python manage.py migrate
Запускаем сервер: python manage.py runserver 0.0.0.0:8000
Готово
----Запуск клиента(android)----
