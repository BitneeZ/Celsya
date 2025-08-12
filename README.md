Проверьте чтобы устройство с клиентом, сервером и сервис были подключены к одной локальной сети

----Запуск сервера(backend)----

Для работы необходимо установить PostgreSQL

В psql создаем Базу данных и пользователя, пример: createdb bezna createuser --interactive psql -c "ALTER USER bezna WITH PASSWORD '12345678';" psql -c "GRANT ALL PRIVILEGES ON DATABASE bezna TO bezna;"

В случае изменения названий базы данных, меняйте название в Celsya/backend/RAI_bezna/setting.py в поле DATABASES на свои

В файле Celsya/backend/roadmap/microservice.py измените ROADMAP_API_URL на ссылку открытого порта шзм4 устройства с сервисом

Переходим в папку проекта и создаем виртуальное окружение python: python -m venv backend_venv

Cкачиваем зависимости: pip install -r requirements.txt

Переходим в backend: cd .\backend

Запускаем миграцию данных: python manage.py makemigrations roadmap

python manage.py migrate

Запускаем сервер: python manage.py runserver 0.0.0.0:8000

Готово

----Запуск клиента(android)----

Скачайте файл Celsya.rar и Android studio(желательно версии 2023.2.1 patch 1)

Разархивируйте Celsya.rar и запустите папку в Android studio(обязательно в пути разирхивации не должно быть кирилицы)

В файле C:\Celsya\app\src\main\java\com\example\celsya\RetrofitClient.kt измените BASE_URL на ipv4 вашего сервера

Скачайте все зависимости, скомпилировуйте приложение

Готово

----Запуск сервиса----
Для того чтобы запустить ии чтобы она локально могла принимать запросы с сервера и отправлять json как ответ надо сделать докер контейнер
ФАЙЛЫ в отдельную папку для создания только их в докер:
* models(папка с моделью)
* Dockerfile
* docker-compose.yml
* llm.py
* prompts.py
* requirements.txt
* roadmap_gen.py
1) Открываем консоль от имени админа
2) Мы должны быть в директории(папке) проекта 
3) пишем в консоль docker build qwen
4) потом docker compose up --build -d
5) ждите
6) чтобы офнуть контейнер надо написать docker compose down
7) а чтобы включить надо прописать docker compose up -d
8) вы научились создавать контейнер в докере УХУ, он готов принимать запросы в локальной сети из бд.
	
P.S. для того чтобы оно всё работало скачайте модель создайте папку models и поместите модель туда и у вас всё должно заработать. У МЕНЯ ЗАРАБОТАЛО!!!!
```python
# !pip install llama-cpp-python

from llama_cpp import Llama

llm = Llama.from_pretrained(
	repo_id="Qwen/Qwen2.5-1.5B-Instruct-GGUF",
	filename="qwen2.5-1.5b-instruct-fp16.gguf",
)

```

