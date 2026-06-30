import httpx
import pytest
from unittest.mock import patch, AsyncMock


class TestSignUpWithEmail:
    @pytest.mark.asyncio
    async def test_sign_up(self, create_user: httpx.Response):
        json_res = create_user.json()

        assert create_user.status_code == 201
        assert json_res["message"] == (
            "Sign up completed successfully."
            "Check your email for verification code and instructions"
        )

    @pytest.mark.asyncio
    async def test_user_exists(
        self, async_client: httpx.AsyncClient, verify_user: httpx.Response
    ):
        sign_up_payload: dict = {
            "email": "user@example.com",
            "password": "test_user_password",
        }

        res: httpx.Response = await async_client.post(
            "/auth/signup", json=sign_up_payload, headers={"env": "test"}
        )

        assert res.status_code == 409

    @pytest.mark.asyncio
    async def test_invalid_email(self, async_client: httpx.AsyncClient):
        sign_up_payload: dict = {
            "email": "invalid_user_email",
            "password": "test_user_password",
        }

        res: httpx.Response = await async_client.post(
            "/auth/signup", json=sign_up_payload, headers={"env": "test"}
        )

        assert res.status_code == 422


class TestLogin:
    @pytest.mark.asyncio
    async def test_login(self, async_client: httpx.AsyncClient, login: httpx.Response):
        json_res = login.json()

        assert login.status_code == 201
        assert "access_token" in json_res["data"]

    @pytest.mark.asyncio
    async def test_user_not_verified(
        self, async_client: httpx.AsyncClient, create_user: httpx.Response
    ):
        login_payload: dict = {
            "email": "user@example.com",
            "password": "test_user_password",
        }

        res: httpx.Response = await async_client.post(
            "/auth/login",
            json=login_payload,
            headers={"env": "test"},
        )

        assert res.status_code == 400

    @pytest.mark.asyncio
    async def test_wrong_email_login(
        self, async_client: httpx.AsyncClient, verify_user: httpx.Response
    ):
        login_payload: dict = {
            "email": "user@example123.com",
            "password": "test_user_password",
        }

        res: httpx.Response = await async_client.post(
            "/auth/login",
            json=login_payload,
            headers={"env": "test"},
        )

        assert res.status_code == 400


class TestSignUpWithGoogle:
    @pytest.mark.asyncio
    async def test_sign_in_google(self, async_client: httpx.AsyncClient):
        url_path: str = "app.api.routers.auth.Request.url_for"
        token_path: str = (
            "app.api.routers.auth.security.oauth.google.authorize_redirect"
        )

        with (
            patch(url_path, new_callable=AsyncMock) as url_patch,
            patch(token_path, new_callable=AsyncMock) as token_patch,
        ):
            token_patch.return_value = None
            res: httpx.Response = await async_client.get(
                "/auth/google", headers={"env": "test"}
            )

        assert res.status_code == 302

        url_patch.assert_called_once()
        token_patch.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_google_callback(self, async_client: httpx.AsyncClient):
        payload: dict = {
            "sub": "randomfakeid",
            "email": "user@example.com",
        }

        token: dict = {"userinfo": payload}

        token_path: str = (
            "app.api.routers.auth.security.oauth.google.authorize_access_token"
        )

        with patch(token_path, new_callable=AsyncMock) as token_patch:
            token_patch.return_value = token

            res: httpx.Response = await async_client.get(
                "/auth/google/callback", headers={"env": "test"}
            )

        json_res = res.json()

        assert res.status_code == 200
        assert "access_token" in json_res

        token_patch.assert_called_once()


class TestSignUpWithGithub:
    @pytest.mark.asyncio
    async def test_successful_sign_in(self, sign_in_with_github: httpx.Response):
        assert sign_in_with_github.status_code == 200
        assert "access_token" in sign_in_with_github.json()

    @pytest.mark.asyncio
    async def test_invalid_state(self, async_client: httpx.AsyncClient):
        state: str = "invalid_github_state"
        res: httpx.Response = await async_client.get(
            f"/auth/github/callback?code=fakegithubcode&state={state}",
            headers={"env": "testing"},
        )


class TestAuthToken:
    @pytest.mark.asyncio
    async def test_get_access_token(
        self, async_client: httpx.AsyncClient, login: httpx.Response
    ):
        res = await async_client.post(
            "/auth/refresh",
            headers={"env": "test"},
        )
        json_res = res.json()

        assert res.status_code == 201
        assert "access_token" in json_res["data"]

    @pytest.mark.asyncio
    async def test_unauthorized_get_access_token(
        self, async_client: httpx.AsyncClient, verify_user: httpx.Response
    ):
        res = await async_client.post(
            "/auth/refresh",
            headers={"env": "test"},
        )

        assert res.status_code == 401


class TestGetCurrentUser:
    @pytest.mark.asyncio
    async def test_get_current_user(
        self, async_client: httpx.AsyncClient, login: httpx.Response
    ):
        access_token = login.json()["data"]["access_token"]

        res: httpx.Response = await async_client.get(
            "/auth/me",
            headers={
                "Authorization": f"Bearer {access_token}",
                "env": "test",
            },
        )

        json_res = res.json()

        assert res.status_code == 200
        assert "user@example.com" == json_res["data"]["email"]

    @pytest.mark.asyncio
    async def test_unauthenticated_user(self, async_client: httpx.AsyncClient):
        res: httpx.Response = await async_client.get(
            "/auth/me",
            headers={"env": "test"},
        )

        assert res.status_code == 401


class TestResendOtp:
    @pytest.mark.asyncio
    async def test_resend_otp_token(
        self, async_client: httpx.AsyncClient, create_user: httpx.Response
    ):
        path: str = "app.api.services.auth_service.send_verification_email.apply_async"

        resend_otp_payload: dict = {
            "email": "user@example.com",
        }

        with patch(path, new_callable=AsyncMock) as email_patch:
            res: httpx.Response = await async_client.post(
                "/auth/verify/resend",
                json=resend_otp_payload,
                headers={"env": "test"},
            )

        json_res = res.json()

        email_patch.assert_called_once()

        assert res.status_code == 201
        assert json_res["status"] == "success"

    @pytest.mark.asyncio
    async def test_invalid_email_otp_token(
        self, async_client: httpx.AsyncClient, create_user: httpx.Response
    ):
        resend_otp_payload: dict = {
            "email": "user@example123.com",
        }

        res: httpx.Response = await async_client.post(
            "/auth/verify/resend",
            json=resend_otp_payload,
            headers={"env": "test"},
        )

        assert res.status_code == 400


class TestApiKey:
    @pytest.mark.asyncio
    async def test_create_api_key(
        self, async_client: httpx.AsyncClient, login: httpx.Response
    ):
        access_token = login.json()["data"]["access_token"]

        res: httpx.Response = await async_client.post(
            "/auth/keys",
            headers={
                "Authorization": f"Bearer {access_token}",
                "env": "test",
            },
        )

        json_res = res.json()

        assert res.status_code == 201
        assert json_res["data"]["key"]

    @pytest.mark.asyncio
    async def test_unauthenticated_create_api_key(
        self, async_client: httpx.AsyncClient, login: httpx.Response
    ):
        res: httpx.Response = await async_client.post(
            "/auth/keys",
            headers={"env": "test"},
        )

        assert res.status_code == 401

    @pytest.mark.asyncio
    async def test_get_all_api_keys(
        self, async_client: httpx.AsyncClient, login: httpx.Response
    ):
        access_token = login.json()["data"]["access_token"]

        await async_client.post(
            "/auth/keys",
            headers={
                "Authorization": f"Bearer {access_token}",
                "env": "test",
            },
        )

        res: httpx.Response = await async_client.get(
            "/auth/keys",
            headers={
                "Authorization": f"Bearer {access_token}",
                "env": "test",
            },
        )

        json_res = res.json()

        assert res.status_code == 200
        assert len(json_res["data"]) >= 1

    @pytest.mark.asyncio
    async def test_get_api_key(
        self, async_client: httpx.AsyncClient, login: httpx.Response
    ):
        access_token = login.json()["data"]["access_token"]

        create_res: httpx.Response = await async_client.post(
            "/auth/keys",
            headers={
                "Authorization": f"Bearer {access_token}",
                "env": "test",
            },
        )

        api_key: str = create_res.json()["data"]["key"]

        res: httpx.Response = await async_client.get(
            "/auth/keys",
            headers={
                "Authorization": f"Bearer {access_token}",
                "env": "test",
            },
        )

        json_res = res.json()

        assert res.status_code == 200
        assert json_res["data"]["key"] == api_key

    @pytest.mark.asyncio
    async def test_api_key_not_found(
        self, async_client: httpx.AsyncClient, login: httpx.Response
    ):
        access_token = login.json()["data"]["access_token"]

        res: httpx.Response = await async_client.get(
            "/auth/keys",
            headers={
                "Authorization": f"Bearer {access_token}",
                "env": "test",
            },
        )

        assert res.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_api_key(
        self, async_client: httpx.AsyncClient, login: httpx.Response
    ):
        access_token = login.json()["data"]["access_token"]

        await async_client.post(
            "/auth/keys",
            headers={
                "Authorization": f"Bearer {access_token}",
                "env": "test",
            },
        )

        res: httpx.Response = await async_client.delete(
            "/auth/keys",
            headers={
                "Authorization": f"Bearer {access_token}",
                "env": "test",
            },
        )

        assert res.status_code == 204


class TestLogout:
    @pytest.mark.asyncio
    async def test_logout(self, async_client: httpx.AsyncClient, login: httpx.Response):
        access_token = login.json()["data"]["access_token"]

        res = await async_client.post(
            "/auth/logout",
            headers={
                "Authorization": f"Bearer {access_token}",
                "env": "test",
            },
        )

        assert res.status_code == 201

        res: httpx.Response = await async_client.get(
            "/auth/me",
            headers={
                "Authorization": f"Bearer {access_token}",
                "env": "test",
            },
        )

        assert res.status_code == 401

    @pytest.mark.asyncio
    async def test_unauthorized_logout(
        self, async_client: httpx.AsyncClient, verify_user: httpx.Response
    ):
        res = await async_client.post(
            "/auth/logout",
            headers={"env": "test"},
        )

        assert res.status_code == 401


class TestDeleteAccount:
    @pytest.mark.asyncio
    async def test_delete_account(
        self, async_client: httpx.AsyncClient, login: httpx.Response
    ):
        access_token = login.json()["data"]["access_token"]

        res = await async_client.delete(
            "/auth",
            headers={
                "Authorization": f"Bearer {access_token}",
                "env": "test",
            },
        )

        assert res.status_code == 204

        login_payload: dict = {
            "email": "user@example.com",
            "password": "test_user_password",
        }

        res: httpx.Response = await async_client.post(
            "/auth/login",
            json=login_payload,
            headers={"env": "test"},
        )

        assert res.status_code == 400

    @pytest.mark.asyncio
    async def test_unauthorized_delete_account(
        self, async_client: httpx.AsyncClient, verify_user: httpx.Response
    ):
        res = await async_client.delete(
            "/auth",
            headers={"env": "test"},
        )

        assert res.status_code == 401
