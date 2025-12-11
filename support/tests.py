from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from support.models import SupportTicket, SupportMessage
from unittest.mock import patch



class SupportViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            password="123456",
            email="test@test.com"
        )
        self.client.login(username="testuser", password="123456")

    def test_support_center_page_loads(self):
        url = reverse("support-center")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


    @patch("core.forms.turnstile.verify_turnstile", return_value=(True, {}))
    def test_support_ticket_create_success(self, mock_turnstile):
        url = reverse("support-center")

        data = {
            "subject": "Test Subject",
            "category": "order",
            "message": "This is a test message",
            "cf-turnstile-response": "dummy-token"
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(SupportTicket.objects.count(), 1)
        self.assertEqual(SupportMessage.objects.count(), 1)

        ticket = SupportTicket.objects.first()
        message = SupportMessage.objects.first()

        self.assertEqual(ticket.subject, "Test Subject")
        self.assertEqual(ticket.user, self.user)
        self.assertEqual(message.message, "This is a test message")


    @patch("core.forms.turnstile.verify_turnstile", return_value=(False, {"error": "invalid"}))
    def test_support_ticket_turnstile_fail(self, mock_turnstile):
        url = reverse("support-center")

        data = {
            "subject": "Blocked Subject",
            "category": "order",
            "message": "Blocked Message",
            "cf-turnstile-response": "dummy-token"
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(SupportTicket.objects.count(), 0)
        self.assertEqual(SupportMessage.objects.count(), 0)