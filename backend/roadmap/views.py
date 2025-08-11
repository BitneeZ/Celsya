from rest_framework import status, permissions, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model, authenticate
from rest_framework.authtoken.models import Token

from .models import AIRequest, Roadmap, Task, Goal
from .serializers import RegisterSerializer, LoginSerializer
from .microservice import get_roadmap_from_service

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
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "email": user.email}, status=status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        user = authenticate(request, email=email, password=password)
        if user is None:
            return Response({"detail": "Неверный email или пароль"}, status=status.HTTP_401_UNAUTHORIZED)

        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "email": user.email}, status=status.HTTP_200_OK)
