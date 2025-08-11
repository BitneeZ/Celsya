from rest_framework import serializers
from .models import AIRequest, Roadmap, RoadmapStep, Task
from django.contrib.auth import get_user_model
from rest_framework.validators import UniqueValidator
from django.contrib.auth.password_validation import validate_password


User = get_user_model()

class AIRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIRequest
        fields = "__all__"
        read_only_fields = ("id","user","status","result","error","created_at","completed_at")


class RoadmapSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roadmap
        fields = ("id","owner","title","description","snapshot","created_at")
        read_only_fields = ("id","owner","created_at")


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = "__all__"
        read_only_fields = ("id","created_at")

class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])

    class Meta:
        model = User
        # если используешь стандартную модель User — оставляем username, но клиент не обязан передавать username;
        # мы можем установить username равным email для совместимости.
        fields = ("email", "password")
        # либо: fields = ("username","email","password","password2") — в зависимости от твоей реализации

    def create(self, validated_data):
        email = validated_data['email']
        password = validated_data['password']
        # Если ваша модель User требует username — установим username == email
        user = User.objects.create_user(username=email, email=email, password=password)
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)