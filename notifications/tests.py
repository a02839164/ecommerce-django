from django.test import TestCase, override_settings
from unittest.mock import patch, Mock
from .email_service import send_email_via_requests


@override_settings(
    DEFAULT_FROM_EMAIL="noreply@test.com",
    SENDGRID_API_KEY="fake-key"
)
class SendEmailViaRequestsTest(TestCase):

    @patch("notifications.email_service.requests.post")
    def test_send_email_success(self, mock_post):
        # ✅ 偽造 requests.post 回傳成功
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.text = "Accepted"
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = send_email_via_requests(
            subject="Test Subject",
            to_email="user@test.com",
            template_base_name="verify_email",
            context={"foo": "bar"}
        )

        # 回傳 True
        self.assertTrue(result)

        # 確認真的有呼叫 requests.post
        mock_post.assert_called_once()

        # 確認呼叫內容含正確 email
        args, kwargs = mock_post.call_args
        self.assertIn("user@test.com", str(kwargs["json"]))
