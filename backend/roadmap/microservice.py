import httpx
import json

# Адрес вашего запущенного в Docker сервиса


def get_roadmap_from_service(topic: str) -> dict:
    """
    Отправляет запрос к API в Docker-контейнере для генерации роадмапа.
    """
    ROADMAP_API_URL = "http://10.245.94.56:8080/generate_roadmap"
    try:
        # Формируем тело запроса в соответствии с моделью RoadmapRequest в main.py
        payload = {"topic": topic, "max_tokens": 2048}

        # Отправляем POST-запрос
        # Устанавливаем таймаут, чтобы не ждать вечно, если сервис "завис"
        with httpx.Client() as client:
            response = client.post(ROADMAP_API_URL, json=payload, timeout=120.0)

        # Проверяем, что запрос прошел успешно (код 200)
        response.raise_for_status()

        # Возвращаем результат в виде словаря
        return response.json(), response.raise_for_status()

    except httpx.HTTPStatusError as e:
        print(f"Ошибка запроса к API: {e.response.status_code}")
        # Здесь можно добавить логирование или обработку ошибок
        return None
    except httpx.RequestError as e:
        print(f"Ошибка соединения с API: {e}")
        return None
