from rest_framework import status, permissions, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model, authenticate
from rest_framework.authtoken.models import Token

from .models import AIRequest, Roadmap, Task, Goal
from .serializers import RegisterSerializer, LoginSerializer
from .microservice import get_roadmap_from_service

import logging

print(">>> LOADED roadmap.views module")

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

User = get_user_model()

@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def generate_roadmap(request, goal_id):
    """
    Простая, минимальная логика:
    - получает goal по id
    - берёт prompt из body 'prompt' или использует goal.title
    - создаёт AIRequest (queued), вызывает микросервис (через get_roadmap_from_service)
    - если микросервис вернул результат — сохраняет AIRequest.result/status и создаёт Roadmap
    - возвращает данные созданного roadmap
    """
    # Получаем goal (если не найден — 404)
    goal = get_object_or_404(Goal, id=goal_id)

    # Авторизованный пользователь или None (мы "забудем про безопасность" как просили)
    user = request.user if getattr(request, "user", None) and request.user.is_authenticated else None

    # Prompt: либо пользовательский, либо заголовок цели
    prompt = request.data.get("prompt") or goal.title or "Roadmap"

    # Создаём запись AIRequest (базовая, queued)
    ai = AIRequest.objects.create(user=user, goal=goal, prompt=prompt, status="queued")

    # Вызов микросервиса
    try:
        svc_resp = get_roadmap_from_service(prompt)
    except Exception as e:
        ai.status = "failed"
        ai.error = f"Exception calling microservice: {e}"
        ai.save(update_fields=["status", "error"])
        return Response({"detail": "Ошибка при вызове микросервиса"}, status=status.HTTP_502_BAD_GATEWAY)

    # Обрабатываем возможные варианты возврата (microservice.py в текущем виде иногда возвращает tuple)
    if svc_resp is None:
        ai.status = "failed"
        ai.error = "Microservice returned None"
        ai.save(update_fields=["status", "error"])
        return Response({"detail": "Microservice error"}, status=status.HTTP_502_BAD_GATEWAY)

    # Если вернулся tuple (json, None) — берем первый элемент, иначе используем как есть
    if isinstance(svc_resp, (list, tuple)):
        gen_result = svc_resp[0]
    else:
        gen_result = svc_resp

    # Сохраняем результат AIRequest
    ai.result = gen_result
    ai.status = "succeeded"
    ai.save()

    # Создаём Roadmap (owner: либо пользователь, либо владелец цели)
    owner = user if user is not None else goal.owner
    roadmap = Roadmap.objects.create(
        owner=owner,
        title=prompt,
        snapshot=gen_result,
        goal=goal,
        ai_request=ai,
    )

    # Возвращаем минимальную информацию о созданном roadmap
    return Response(
        {
            "id": str(roadmap.id),
            "title": roadmap.title,
            "snapshot": roadmap.snapshot
        },
        status=status.HTTP_201_CREATED
    )

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
