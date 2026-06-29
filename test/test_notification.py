import uuid
import httpx
import pytest
from unittest.mock import patch, MagicMock


def get_notification_payload():
    return {
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
        "payload": {}
    }


class TestSendNotification:
    @pytest.mark.asyncio
    async def test_create_notification(
        self, async_client: httpx.AsyncClient, login: httpx.Response
    ):
        path: str = "app.worker.tasks.email.email"
        with patch(path, new_callable=MagicMock) as _:
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

            json_res = res.json()

            assert res.status_code == 202
            assert (
                json_res["data"]["idempotency_key"]
                == notification_payload["idempotency_key"]
            )

    @pytest.mark.asyncio
    async def test_existing_notification(
        self, async_client: httpx.AsyncClient, login: httpx.Response
    ):
        path: str = "app.worker.tasks.email.email"
        with patch(path, new_callable=MagicMock) as _:
            access_token = login.json()["data"]["access_token"]

            notification_payload: dict = get_notification_payload()
            await async_client.post(
                "/notifications",
                json=notification_payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "env": "test",
                },
            )

            res: httpx.Response = await async_client.post(
                "/notifications",
                json=notification_payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "env": "test",
                },
            )

            assert res.status_code == 409

    @pytest.mark.asyncio
    async def test_unauthenticated_notification(self, async_client: httpx.AsyncClient):
        path: str = "app.worker.tasks.email.email"
        notification_payload: dict = get_notification_payload()

        with patch(path, new_callable=MagicMock) as _:
            res: httpx.Response = await async_client.post(
                "/notifications",
                json=notification_payload,
                headers={"env": "test"},
            )

            assert res.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_payload(
        self, async_client: httpx.AsyncClient, login: httpx.Response
    ):
        path: str = "app.worker.tasks.email.email"
        with patch(path, new_callable=MagicMock) as email_mock:
            access_token = login.json()["data"]["access_token"]
            notification_payload: dict = get_notification_payload()

            notification_payload["type"] = "bulk"
            res: httpx.Response = await async_client.post(
                "/notifications",
                json=notification_payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "env": "test",
                },
            )

            assert res.status_code == 400

class TestWebhookNotification:
    @pytest.mark.asyncio
    async def test_create_notification(
        self, async_client: httpx.AsyncClient, login: httpx.Response
    ):
        path: str = "app.worker.tasks.webhook.http_request"
        with patch(path, new_callable=MagicMock) as _:
            access_token = login.json()["data"]["access_token"]

            notification_payload: dict = get_webhook_payload()
            res: httpx.Response = await async_client.post(
                "/notifications/webhook",
                json=notification_payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "env": "test",
                },
            )

            json_res = res.json()

            assert res.status_code == 202
            assert (
                json_res["data"]["idempotency_key"]
                == notification_payload["idempotency_key"]
            )

    @pytest.mark.asyncio
    async def test_existing_notification(
        self, async_client: httpx.AsyncClient, login: httpx.Response
    ):
        path: str = "app.worker.tasks.webhook.http_request"
        with patch(path, new_callable=MagicMock) as _:
            access_token = login.json()["data"]["access_token"]

            notification_payload: dict = get_webhook_payload()
            await async_client.post(
                "/notifications/webhook",
                json=notification_payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "env": "test",
                },
            )

            res: httpx.Response = await async_client.post(
                "/notifications/webhook",
                json=notification_payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "env": "test",
                },
            )

            assert res.status_code == 409

class TestGetNotification:
    @pytest.mark.asyncio
    async def test_get_notification(
        self, async_client: httpx.AsyncClient, login: httpx.Response
    ):
        path: str = "app.worker.tasks.email.email"
        with patch(path, new_callable=MagicMock) as _:
            access_token = login.json()["data"]["access_token"]
            notification_payload: dict = get_notification_payload()

            create_res: httpx.Response = await async_client.post(
                "/notifications",
                json=notification_payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "env": "test",
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
