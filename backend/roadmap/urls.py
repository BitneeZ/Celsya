from django.urls import path
from . import views
from .views import RegisterView, LoginView

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path('goals/<uuid:goal_id>/generate/', views.generate_roadmap, name='generate_roadmap'),
    path('ai_request/<uuid:ai_request_id>/status/', views.ai_request_status, name='ai_request_status'),
    path('tasks/<uuid:task_id>/complete/', views.complete_task, name='complete_task'),
]
