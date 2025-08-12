from rest_framework import status, permissions, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model, authenticate
from rest_framework.authtoken.models import Token

from .models import AIRequest, Roadmap, Task, Goal
from .serializers import RegisterSerializer, LoginSerializer
from .microservice import get_roadmap_from_service
from django.db import models as djmodels
from django.utils import timezone
from django.db import IntegrityError

import logging

print(">>> LOADED roadmap.views module")

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

User = get_user_model()

@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def generate_from_prompt(request):
    """
    Ожидает JSON: {"prompt": "текст запроса для микросервиса"}
    Логика:
      - создаёт Goal (owner=request.user, title=prompt)
      - создаёт AIRequest(status='queued')
      - вызывает микросервис get_roadmap_from_service(prompt)
      - сохраняет результат в AIRequest, создаёт Roadmap
      - возвращает клиенту JSON, который вернул микросервис
    """
    user = request.user
    data = request.data or {}
    prompt = data.get("prompt")
    if not prompt or not isinstance(prompt, str):
        return Response({"detail": "Field 'prompt' is required (string)."}, status=status.HTTP_400_BAD_REQUEST)

    # 3) Вызов микросервиса
    try:
        svc_resp, _ = get_roadmap_from_service(prompt)
    except Exception as exc:
        # помечаем AIRequest как failed и возвращаем ошибку
        print(exc)

    # защитимся от None и tuple/list возвратов
    if svc_resp is None:
        return Response({"detail": "Microservice returned no data"}, status=status.HTTP_502_BAD_GATEWAY)

    gen_result = svc_resp[0] if isinstance(svc_resp, (list, tuple)) and len(svc_resp) > 0 else svc_resp
    print(gen_result)

    # 5) Создаём Roadmap (owner=user)
    try:
        roadmap = Roadmap.objects.create(
            owner=user,
            title=prompt,
            snapshot=gen_result,
        )
    except Exception:
        return Response(gen_result, status=status.HTTP_200_OK)

    # 6) Возвращаем клиенту ответ микросервиса (как есть)
    return Response(gen_result, status=status.HTTP_200_OK)

@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def ai_request_status(request, ai_request_id):
    """
    Возвращает статус AIRequest. Для простоты — без жёсткой проверки пользователей.
    """
    ai = get_object_or_404(AIRequest, id=ai_request_id)
    # Отдаём минимальный набор полей
    return Response({
        "id": str(ai.id),
        "status": ai.status,
        "error": ai.error,
        "result": ai.result,
        "created_at": ai.created_at,
        "completed_at": ai.completed_at,
    })

@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def complete_task(request, task_id):
    """
    Помечает задачу как выполненную (для MVP — без сложной безопасности).
    """
    task = get_object_or_404(Task, id=task_id)
    # В простом варианте — позволяем владельцу roadmap помечать задачи
    if task.step.roadmap.owner and request.user != task.step.roadmap.owner:
        return Response({"detail": "Not allowed"}, status=status.HTTP_403_FORBIDDEN)

    task.status = "done"
    task.save(update_fields=["status"])
    return Response({"detail": "ok", "task_id": str(task.id)}, status=status.HTTP_200_OK)


# ========== Auth endpoints (минимальные) ==========
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        # Быстрая трассировка — гарантированно попадёт в stdout
        print(">>> RegisterView.create entered")

        # Логируем заголовки и тело (raw + parsed)
        try:
            headers = {k: v for k, v in request.META.items() if k.startswith("HTTP_") or k in ("CONTENT_TYPE", "CONTENT_LENGTH")}
            logger.debug("Register request PATH=%s METHOD=%s", request.path, request.method)
            logger.debug("Register request headers: %s", headers)
            logger.debug("Register request.data (parsed): %s", request.data)
            try:
                raw = request.body.decode("utf-8")
            except Exception:
                raw = "<non-decodable>"
            logger.debug("Register raw body: %s", raw)
        except Exception:
            logger.exception("Failed to log incoming registration request")

        # Создаём сериализатор и валидируем без raise_exception, чтобы получить serializer.errors
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            # Логируем ошибки валидации и возвращаем их в ответе (чтобы клиент видел, что не так)
            logger.warning("Register validation failed: %s", serializer.errors)
            # Маскируем пароль в логах/ответе (безопаснее)
            errors_for_response = dict(serializer.errors)
            try:
                if 'password' in errors_for_response:
                    # оставляем текст ошибки, но НЕ возвращаем сам пароль
                    pass
            except Exception:
                pass

            return Response({"detail": "validation_error", "errors": errors_for_response}, status=status.HTTP_400_BAD_REQUEST)

        # Если валидно — сохраняем и возвращаем токен
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        logger.info("New user created: %s", user.email)
        return Response({"token": token.key, "email": user.email}, status=status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        data = dict(request.data or {})
        masked = dict(data)
        if "password" in masked:
            masked["password"] = "***"
        logger.debug("Login attempt (masked): %s", masked)

        email = data.get("email")
        password = data.get("password")
        if not email or not password:
            return Response({"detail": "email and password required"}, status=status.HTTP_400_BAD_REQUEST)

        # Попробуем разные варианты authenticate и залогируем результат
        user = None
        try:
            user = authenticate(request, username=email, password=password)
            logger.debug("authenticate(request, username=...) returned: %r", user)
        except Exception:
            logger.exception("authenticate(request, username=...) raised")

        if user is None:
            try:
                user = authenticate(request, email=email, password=password)
                logger.debug("authenticate(request, email=...) returned: %r", user)
            except Exception:
                logger.exception("authenticate(request, email=...) raised")

        # Если authenticate вернул None, попробуем явный fallback (поиск + check_password)
        if user is None:
            try:
                u = User.objects.filter(email__iexact=email).first()
                logger.debug("Fallback lookup user by email returned: %r", u)
                if u is not None and u.check_password(password) and u.is_active:
                    user = u
                    logger.debug("Fallback check_password succeeded for user %r", u)
            except Exception:
                logger.exception("Error during fallback user lookup")

        if user is None:
            logger.info("Login failed for email=%s", email)
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        token, _ = Token.objects.get_or_create(user=user)
        logger.info("Login success for user=%s", getattr(user, "email", user.username))
        return Response({"token": token.key, "email": getattr(user, "email", user.username)}, status=status.HTTP_200_OK)
