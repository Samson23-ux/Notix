import pytest
from uuid import uuid4
from unittest.mock import patch, MagicMock
from celery.exceptions import Retry, Reject


from app.api.models.email import Email
from app.worker.tasks.dlq import monitor_dlq
from app.core.exceptions import MaxRetriesError
from app.api.models.notification import Notification
from app.worker.tasks.webhook import deliver_webhook_task
from app.worker.tasks.digest import collect_and_send_digests
from app.worker.tasks.email import (
    send_email_task,
    send_verification_email,
    send_critical_email_task,
)

EMAIL_PATH = "app.worker.get_email_service"
REQUEST_PATH = "app.worker.get_request_service"
NOTIS_PATH = "app.worker.get_notification_service"
CHANNEL_PATH = "app.worker.tasks.dlq.get_event_channel"


def get_email_mock():
    email = MagicMock()
    email.get_processed_email.return_value = Email(
        id=uuid4(), processed_email="user@example.com"
    )

    return email


def get_notis_mock(type: str):
    notis = MagicMock()

    notis_db = Notification(
        id=uuid4(), idempotency_key="test-idempotency-key", type=type
    )

    notis._get_notification.return_value = notis_db
    notis.get_digest_notifications.return_value = [notis_db]

    return notis


def get_channel_mock():
    channel = MagicMock()
    channel.sync_queue_depth.return_value = 10

    return channel


def get_request_mock():
    request = MagicMock()
    return request


class TestVerificationEmail:
    @pytest.mark.asyncio
    async def test_send_verification_email(self, celery_task_config):
        with patch(EMAIL_PATH) as email_mock:
            email_mock.return_value = get_email_mock()

            send_verification_email.apply_async(
                priority=5,
                kwargs={
                    "email_id": uuid4(),
                    "recipient_email": "user@example.com",
                    "user_id": uuid4(),
                },
            )

            email_mock.assert_called()

    @pytest.mark.asyncio
    async def test_retry_email(self, celery_task_config):
        with pytest.raises(Retry) as exc:
            send_verification_email.apply_async(
                priority=5,
                kwargs={
                    "email_id": uuid4(),
                    "recipient_email": "user@example.com",
                    "user_id": uuid4(),
                },
            )

        assert isinstance(exc.value.exc, MaxRetriesError)


class TestNotificationEmail:
    @pytest.mark.asyncio
    async def test_send_email_task(self, celery_task_config):
        with patch(EMAIL_PATH) as email_mock, patch(NOTIS_PATH) as notis_mock:
            notis_mock.return_value = get_notis_mock("email")
            email_mock.return_value = get_email_mock()

            send_email_task.apply_async(
                priority=5,
                kwargs={
                    "notification_id": uuid4(),
                    "idempotency_key": "test-idempotency-key",
                    "recipient_email": "user@example.com",
                    "subject": "test-email-subject",
                    "body": "test-email-body",
                },
            )

            email_mock.assert_called()
            notis_mock.assert_called()

    @pytest.mark.asyncio
    async def test_retry_email_task(self, celery_task_config):
        with pytest.raises(Retry) as exc, patch(NOTIS_PATH) as notis_mock:
            notis_mock.return_value = get_notis_mock("email")
            send_email_task.apply_async(
                priority=5,
                kwargs={
                    "notification_id": uuid4(),
                    "idempotency_key": "test-idempotency-key",
                    "recipient_email": "user@example.com",
                    "subject": "test-email-subject",
                    "body": "test-email-body",
                },
            )

        notis_mock.assert_called()
        assert isinstance(exc.value.exc, MaxRetriesError)

    @pytest.mark.asyncio
    async def test_send_critical_email_task(self, celery_task_config):
        with patch(EMAIL_PATH) as email_mock, patch(NOTIS_PATH) as notis_mock:
            notis_mock.return_value = get_notis_mock("email")
            email_mock.return_value = get_email_mock()

            send_critical_email_task.apply_async(
                priority=10,
                kwargs={
                    "notification_id": uuid4(),
                    "idempotency_key": "test-idempotency-key",
                    "recipient_email": "user@example.com",
                    "subject": "test-email-subject",
                    "body": "test-email-body",
                },
            )

            email_mock.assert_called()
            notis_mock.assert_called()

    @pytest.mark.asyncio
    async def test_retry_critical_email_task(self, celery_task_config):
        with pytest.raises(Retry) as exc, patch(NOTIS_PATH) as notis_mock:
            notis_mock.return_value = get_notis_mock("email")
            send_critical_email_task.apply_async(
                priority=10,
                kwargs={
                    "notification_id": uuid4(),
                    "idempotency_key": "test-idempotency-key",
                    "recipient_email": "user@example.com",
                    "subject": "test-email-subject",
                    "body": "test-email-body",
                },
            )

        notis_mock.assert_called()
        assert isinstance(exc.value.exc, MaxRetriesError)


class TestWebhookNotification:
    @pytest.mark.asyncio
    async def test_deliver_webhook_task(self, celery_task_config):
        with patch(REQUEST_PATH) as req_mock, patch(NOTIS_PATH) as notis_mock:
            req_mock.return_value = get_request_mock()
            notis_mock.return_value = get_notis_mock("webhook")

            deliver_webhook_task.apply_async(
                priority=5,
                kwargs={
                    "notification_id": uuid4(),
                    "idempotency_key": "test-idempotency-key",
                    "secret": "test-webhook-secret",
                    "webhook_url": "test-webhook-url",
                    "payload": {"data": "test-wbehook-data"},
                },
            )

            req_mock.assert_called()
            notis_mock.assert_called()

    @pytest.mark.asyncio
    async def test_retry_deliver_webhook_task(self, celery_task_config):
        with pytest.raises(Retry) as exc, patch(NOTIS_PATH) as notis_mock:
            notis_mock.return_value = get_notis_mock("webhook")
            deliver_webhook_task.apply_async(
                priority=5,
                kwargs={
                    "notification_id": uuid4(),
                    "idempotency_key": "test-idempotency-key",
                    "secret": "test-webhook-secret",
                    "webhook_url": "http://test-webhook-url",
                    "payload": {"data": "test-wbehook-data"},
                },
            )

        notis_mock.assert_called()
        assert isinstance(exc.value.exc, MaxRetriesError)


class TestDigestNotification:
    @pytest.mark.asyncio
    async def test_collect_and_send_digests(self, celery_task_config):
        with patch(EMAIL_PATH) as email_mock, patch(NOTIS_PATH) as notis_mock:
            notis_mock.return_value = get_notis_mock("digest")
            email_mock.return_value = get_email_mock()

            collect_and_send_digests.apply_async(priority=5)

            email_mock.assert_called()
            notis_mock.assert_called()

    @pytest.mark.asyncio
    async def test_retry_email_task(self, celery_task_config):
        with pytest.raises(Retry) as exc, patch(NOTIS_PATH) as notis_mock:
            notis_mock.return_value = get_notis_mock("digest")
            collect_and_send_digests.apply_async(priority=5)

        notis_mock.assert_called()
        assert isinstance(exc.value.exc, MaxRetriesError)

class TestDlq:
    @pytest.mark.asyncio
    async def test_monitor_dlq(self, celery_task_config):
        with patch(CHANNEL_PATH) as channel_mock:
            channel_mock.return_value = get_channel_mock()

            monitor_dlq()

            channel_mock.assert_called()
