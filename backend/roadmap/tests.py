from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from unittest.mock import patch

from .models import AIRequest, Roadmap, Goal, User


class GenerateRoadmapTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='password123',
            username='test@example.com'
        )
        self.client.force_authenticate(user=self.user)

        # Заполняем все обязательные поля Goal
        self.goal = Goal.objects.create(
            owner=self.user,
            title="Как выучить джанго?",
            status="draft"
        )

    @patch("roadmap.views.get_roadmap_from_service")
    def test_generate_roadmap_creates_roadmap(self, mock_get_roadmap):
        """
        Проверяет, что при успешном ответе микросервиса создаются Roadmap и AIRequest
        """
        mock_payload = {"steps": [{"title": "Первый шаг"}, {"title": "Второй шаг"}]}
        mock_get_roadmap.return_value = mock_payload

        url = reverse("generate_roadmap", args=[self.goal.id])
        response = self.client.post(url, data={}, format="json")

        self.assertEqual(
            response.status_code, 201,
            msg=f"Unexpected response: {getattr(response, 'data', response.content)}"
        )

        roadmap_id = response.data["id"]
        roadmap = Roadmap.objects.get(id=roadmap_id)
        self.assertEqual(roadmap.goal.id, self.goal.id)
        self.assertEqual(roadmap.snapshot, mock_payload)

        ai = AIRequest.objects.filter(goal=self.goal).first()
        self.assertIsNotNone(ai)
        self.assertEqual(ai.status, "succeeded")
        self.assertEqual(ai.result, mock_payload)