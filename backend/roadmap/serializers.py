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
    username = serializers.CharField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )

    class Meta:
        model = User
        fields = ("username", "email", "password")

    def create(self, validated_data):
        username = validated_data['username']
        email = validated_data['email']
        password = validated_data['password']
        user = User.objects.create_user(username=username, email=email, password=password)
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)