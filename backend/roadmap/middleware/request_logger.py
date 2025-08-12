import logging

logger = logging.getLogger("request_logger")

class RequestLoggerMiddleware:
    """
    Простая middleware для логирования входящих HTTP-запросов.
    Включите её в MIDDLEWARE (в settings.py) чтобы логировать все запросы.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        print(">>> RequestLoggerMiddleware invoked for path:", request.path)
        try:
            if request.method in ("POST", "PUT", "PATCH"):
                # заголовки
                headers = {k: v for k, v in request.META.items() if k.startswith("HTTP_") or k in ("CONTENT_TYPE","CONTENT_LENGTH")}
                logger.info("Incoming request %s %s", request.method, request.get_full_path())
                logger.info("Headers: %s", headers)
                # request.body может быть большим; осторожно
                try:
                    body = request.body.decode("utf-8")
                except Exception:
                    body = "<non-decodable>"
                # Не выводим огромные тела целиком — обрезаем
                max_len = 10000
                if len(body) > max_len:
                    body = body[:max_len] + "...(truncated)"
                logger.info("Body: %s", body)
        except Exception:
            logger.exception("Failed to log request")

        response = self.get_response(request)
        return response
