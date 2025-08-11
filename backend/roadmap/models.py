import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.conf import settings


# ---------------------------
# Пользователь (кастомный)
# ---------------------------
class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # AbstractUser уже содержит username, email, password, first_name, last_name
    locale = models.CharField(max_length=10, blank=True, null=True)
    settings = models.JSONField(blank=True, null=True)
    last_active_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    email = models.EmailField(unique=True, blank=False, null=False)
    username = models.CharField(max_length=150, unique=False, blank=True, null=True)

    USERNAME_FIELD = 'email'

    REQUIRED_FIELDS = []
    def mark_active(self):
        self.last_active_at = timezone.now()
        self.save(update_fields=["last_active_at"])

    class Meta:
        db_table = "users"
        indexes = [
            models.Index(fields=["email"]),
        ]


# ---------------------------
# Цели
# ---------------------------
class Goal(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("active", "Active"),
        ("archived", "Archived"),
    ]

    VISIBILITY_CHOICES = [
        ("private", "Private"),
        ("shared", "Shared"),
        ("public", "Public"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="goals")
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    meta = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "goals"
        indexes = [
            models.Index(fields=["owner"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return self.title


# ---------------------------
# AI-запросы (логирование генераций)
# ---------------------------
class AIRequest(models.Model):
    STATUS_CHOICES = [
        ("queued", "Queued"),
        ("running", "Running"),
        ("succeeded", "Succeeded"),
        ("failed", "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="ai_requests")
    goal = models.ForeignKey(Goal, on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_requests")
    prompt = models.TextField(blank=True)
    model = models.CharField(max_length=200, blank=True)
    params = models.JSONField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="queued")
    result = models.JSONField(blank=True, null=True)  # raw output / parsed roadmap
    error = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "ai_requests"
        indexes = [
            models.Index(fields=["status", "created_at"]),
        ]


# ---------------------------
# Roadmap
# ---------------------------
class Roadmap(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
        ("archived", "Archived"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name="roadmap")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="roadmap")
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    ai_request = models.ForeignKey(AIRequest, null=True, blank=True, on_delete=models.SET_NULL, related_name="generated_roadmap")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    snapshot = models.JSONField(blank=True, null=True)  # полное дерево для быстрого восстановления
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "roadmap"
        indexes = [
            models.Index(fields=["goal"]),
            models.Index(fields=["owner"]),
        ]

    def __str__(self):
        return self.title

# ---------------------------
# Шаги roadmap (иерархия)
# ---------------------------
class RoadmapStep(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    roadmap = models.ForeignKey(Roadmap, on_delete=models.CASCADE, related_name="steps")
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="children")
    title = models.CharField(max_length=400)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    duration_days = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=30, default="todo")
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_steps")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "roadmap_steps"
        indexes = [
            models.Index(fields=["roadmap", "parent"]),
        ]

    def __str__(self):
        return self.title


# ---------------------------
# Задачи (main / side)
# ---------------------------
class Task(models.Model):
    TYPE_CHOICES = [
        ("main", "Main"),
        ("side", "Side"),
    ]
    STATUS_CHOICES = [
        ("todo", "To Do"),
        ("in_progress", "In Progress"),
        ("done", "Done"),
        ("blocked", "Blocked"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    step = models.ForeignKey(RoadmapStep, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=400)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default="main")
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="todo")
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_tasks")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tasks"
        indexes = [
            models.Index(fields=["step", "type", "status"]),
        ]

    def __str__(self):
        return self.title

