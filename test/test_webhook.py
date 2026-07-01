import httpx
import pytest
from uuid import uuid7


class TestCreateEndpoint:
    @pytest.mark.asyncio
    async def test_create_endpoint(self, async_client: httpx.AsyncClient, login: httpx.Response):
        access_token = login.json()["data"]["access_token"]

        webhook_payload: dict = {"endpoint": "fake-webhook-url"}
        res: httpx.Response = await async_client.post(
            "/webhook",
            json=webhook_payload,
            headers={
                "Authorization": f"Bearer {access_token}",
                "env": "test",
            },
        )

        json_res = res.json()

        assert res.status_code == 201
        assert json_res["data"]["endpoint"] == "fake-webhook-url"

    @pytest.mark.asyncio
    async def test_endpoint_exists(self, async_client: httpx.AsyncClient, login: httpx.Response):
        access_token = login.json()["data"]["access_token"]

        webhook_payload: dict = {"endpoint": "fake-webhook-url"}
        await async_client.post(
            "/webhook",
            json=webhook_payload,
            headers={
                "Authorization": f"Bearer {access_token}",
                "env": "test",
            },
        )

        res: httpx.Response = await async_client.post(
            "/webhook",
            json=webhook_payload,
            headers={
                "Authorization": f"Bearer {access_token}",
                "env": "test",
            },
        )

        assert res.status_code == 409

class TestDeleteEndpoint:
    @pytest.mark.asyncio
    async def test_delete_endpoint(self, async_client: httpx.AsyncClient, login: httpx.Response):
        access_token = login.json()["data"]["access_token"]

        webhook_payload: dict = {"endpoint": "fake-webhook-url"}
        create_res: httpx.Response = await async_client.post(
            "/webhook",
            json=webhook_payload,
            headers={
                "Authorization": f"Bearer {access_token}",
                "env": "test",
            },
        )

        endpoint_id = create_res.json()["data"]["id"]

        res: httpx.Response = await async_client.delete(
            f"/webhook/{endpoint_id}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "env": "test",
            },
        )

        assert res.status_code == 204

    @pytest.mark.asyncio
    async def test_endpoint_not_found(self, async_client: httpx.AsyncClient, login: httpx.Response):
        access_token = login.json()["data"]["access_token"]
        endpoint_id = uuid7()

        res: httpx.Response = await async_client.delete(
            f"/webhook/{endpoint_id}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "env": "test",
            },
        )

        assert res.status_code == 404
