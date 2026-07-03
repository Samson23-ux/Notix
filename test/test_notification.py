import uuid
import httpx
import pytest
import secrets
from unittest.mock import patch, MagicMock

BASE_PATH = "app.api.services.notification"


def get_notification_payload():
    return {
        "recipient": "user@example.com",
        "idempotency_key": "test-send-email",
        "type": "email",
        "subject": "Integration Test",
        "body": "This is a test email for integration test",
    }


def get_webhook_payload():
    return {
        "idempotency_key": "test-send-email",
        "type": "email",
        "webhook_url": "fake-webhook-url",
        "payload": {},
    }


class TestSendNotification:
    TASK_PATH = f"{BASE_PATH}.send_email_task.apply_async"

    @pytest.mark.asyncio
    async def test_create_notification(
        self, async_client: httpx.AsyncClient, login: httpx.Response
    ):
        with patch(self.TASK_PATH, new_callable=MagicMock) as email_mock:
            access_token = login.json()["data"]["access_token"]
            notification_payload: dict = get_notification_payload()

            api_key_res: httpx.Response = await async_client.post(
                "/auth/keys",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "env": "test",
                },
            )

            api_key: str = api_key_res.json()["data"]["key"]

            res: httpx.Response = await async_client.post(
                "/notifications",
                json=notification_payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "env": "test",
                    "api_key": api_key,
                },
            )

            json_res = res.json()

            email_mock.assert_called_once()
            assert res.status_code == 202
            assert (
                json_res["data"]["idempotency_key"]
                == notification_payload["idempotency_key"]
            )

    @pytest.mark.asyncio
    async def test_existing_notification(
        self, async_client: httpx.AsyncClient, login: httpx.Response
    ):
        with patch(self.TASK_PATH, new_callable=MagicMock) as email_mock:
            access_token = login.json()["data"]["access_token"]
            notification_payload: dict = get_notification_payload()

            api_key_res: httpx.Response = await async_client.post(
                "/auth/keys",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "env": "test",
                },
            )

            api_key: str = api_key_res.json()["data"]["key"]

            await async_client.post(
                "/notifications",
                json=notification_payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "env": "test",
                    "api_key": api_key,
                },
            )

            res: httpx.Response = await async_client.post(
                "/notifications",
                json=notification_payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "env": "test",
                    "api_key": api_key,
                },
            )

            email_mock.assert_called_once()
            assert res.status_code == 409

    @pytest.mark.asyncio
    async def test_missing_api_key(
        self, async_client: httpx.AsyncClient, login: httpx.Response
    ):
        access_token = login.json()["data"]["access_token"]
        notification_payload: dict = get_notification_payload()

        res: httpx.Response = await async_client.post(
            "/notifications",
            json=notification_payload,
            headers={
                "Authorization": f"Bearer {access_token}",
                "env": "test",
            },
        )

        assert res.status_code == 404

    @pytest.mark.asyncio
    async def test_unauthenticated_notification(
        self, async_client: httpx.AsyncClient, login: httpx.Response
    ):
        access_token = login.json()["data"]["access_token"]
        notification_payload: dict = get_notification_payload()

        api_key_res: httpx.Response = await async_client.post(
            "/auth/keys",
            headers={
                "Authorization": f"Bearer {access_token}",
                "env": "test",
            },
        )

        api_key: str = api_key_res.json()["data"]["key"]

        res: httpx.Response = await async_client.post(
            "/notifications",
            json=notification_payload,
            headers={"env": "test", "api_key": api_key},
        )

        assert res.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_payload(
        self, async_client: httpx.AsyncClient, login: httpx.Response
    ):
        access_token = login.json()["data"]["access_token"]
        notification_payload: dict = get_notification_payload()

        api_key_res: httpx.Response = await async_client.post(
            "/auth/keys",
            headers={
                "Authorization": f"Bearer {access_token}",
                "env": "test",
            },
        )

        api_key: str = api_key_res.json()["data"]["key"]

        notification_payload["type"] = "bulk"
        res: httpx.Response = await async_client.post(
            "/notifications",
            json=notification_payload,
            headers={
                "Authorization": f"Bearer {access_token}",
                "env": "test",
                "api_key": api_key,
            },
        )

        assert res.status_code == 422


class TestWebhookNotification:
    TASK_PATH = f"{BASE_PATH}.deliver_webhook_task.apply_async"

    @pytest.mark.asyncio
    async def test_create_notification(
        self, async_client: httpx.AsyncClient, login: httpx.Response
    ):
        with patch(self.TASK_PATH, new_callable=MagicMock) as webhook_mock:
            access_token = login.json()["data"]["access_token"]

            webhook_payload: dict = {"endpoint": "fake-webhook-url"}

            api_key_res: httpx.Response = await async_client.post(
                "/auth/keys",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "env": "test",
                },
            )

            api_key: str = api_key_res.json()["data"]["key"]

            await async_client.post(
                "/webhook",
                json=webhook_payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "env": "test",
                },
            )

            notification_payload: dict = get_webhook_payload()
            res: httpx.Response = await async_client.post(
                "/notifications/webhook",
                json=notification_payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "env": "test",
                    "api_key": api_key,
                },
            )

            json_res = res.json()

            webhook_mock.assert_called_once()
            assert res.status_code == 202
            assert (
                json_res["data"]["idempotency_key"]
                == notification_payload["idempotency_key"]
            )

    @pytest.mark.asyncio
    async def test_existing_notification(
        self, async_client: httpx.AsyncClient, login: httpx.Response
    ):
        with patch(self.TASK_PATH, new_callable=MagicMock) as webhook_mock:
            access_token = login.json()["data"]["access_token"]

            api_key_res: httpx.Response = await async_client.post(
                "/auth/keys",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "env": "test",
                },
            )

            api_key: str = api_key_res.json()["data"]["key"]

            webhook_payload: dict = {"endpoint": "fake-webhook-url"}
            await async_client.post(
                "/webhook",
                json=webhook_payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "env": "test",
                    "api_key": api_key,
                },
            )

            notification_payload: dict = get_webhook_payload()
            await async_client.post(
                "/notifications/webhook",
                json=notification_payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "env": "test",
                    "api_key": api_key,
                },
            )

            res: httpx.Response = await async_client.post(
                "/notifications/webhook",
                json=notification_payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "env": "test",
                    "api_key": api_key,
                },
            )

            webhook_mock.assert_called_once()
            assert res.status_code == 409


class TestGetNotification:
    TASK_PATH = f"{BASE_PATH}.send_email_task.apply_async"

    @pytest.mark.asyncio
    async def test_get_notification(
        self, async_client: httpx.AsyncClient, login: httpx.Response
    ):
        with patch(self.TASK_PATH, new_callable=MagicMock) as email_mock:
            access_token = login.json()["data"]["access_token"]
            notification_payload: dict = get_notification_payload()

            api_key_res: httpx.Response = await async_client.post(
                "/auth/keys",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "env": "test",
                },
            )

            api_key: str = api_key_res.json()["data"]["key"]

            create_res: httpx.Response = await async_client.post(
                "/notifications",
                json=notification_payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "env": "test",
                    "api_key": api_key
                },
            )

            notification_id = create_res.json()["data"]["id"]
            res: httpx.Response = await async_client.get(
                f"/notifications/{notification_id}",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "env": "test",
                },
            )

            json_res = res.json()

            email_mock.assert_called_once()
            assert res.status_code == 200
            assert (
                json_res["data"]["idempotency_key"]
                == notification_payload["idempotency_key"]
            )

    @pytest.mark.asyncio
    async def test_notification_not_found(
        self, async_client: httpx.AsyncClient, login: httpx.Response
    ):
        notification_id = uuid.uuid4()
        access_token = login.json()["data"]["access_token"]

        res: httpx.Response = await async_client.get(
            f"/notifications/{notification_id}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "env": "test",
            },
        )

        assert res.status_code == 404
