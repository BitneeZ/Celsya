FROM python:3.10-slim
RUN apt-get update && apt-get install -y --no-install-recommends build-essential
WORKDIR /app

# 1. Копируем ТОЛЬКО файл с зависимостями.
# Этот слой будет пересобираться, только если изменится сам requirements.txt.
COPY requirements.txt requirements.txt

# 2. Устанавливаем зависимости.
# Docker видит, что requirements.txt не изменился (шаг 1 взят из кэша),
# значит, и этот шаг он тоже возьмет из кэша.
RUN pip install --no-cache-dir -r requirements.txt

# 3. И только ТЕПЕРЬ копируем остальные файлы проекта.
# Если вы измените свой .py код, только этот слой и последующие будут
# пересобраны. Установка зависимостей затронута не будет.
COPY . .

EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]