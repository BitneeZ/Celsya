# accounts/auth_backends.py
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class EmailBackend(BaseBackend):
    """
    Простая аутентификация по email.
    Не меняет поведение ModelBackend для username — просто добавляет возможность логина по email.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        # username может быть email при вызове authenticate(email=..., password=...)
        email = kwargs.get('email') or username
        if email is None or password is None:
            return None
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return None
        if user.check_password(password):
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
