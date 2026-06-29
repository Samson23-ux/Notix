import httpx
from app.core.exceptions import CheckTimeoutError


class Request:
    def __init__(self, async_client: httpx.AsyncClient, sync_client: httpx.Client):
        self._sync_client = sync_client
        self._async_client = async_client

    MAXIMUM_RETRIES = 5

    async def post(
        self,
        url: str,
        data: dict = None,
        json: dict = None,
        headers: dict = None,
        cookies: dict = None,
    ) -> httpx.Response:
        curr_retries: int = 0
        status: str = "failure"

        while curr_retries < self.MAXIMUM_RETRIES and status == "failure":
            try:
                res: httpx.Response = await self._async_client.post(
                    url, data, json, headers, cookies
                )

                status = "success"
                return res
            except httpx.ConnectError, httpx.ConnectTimeout:
                curr_retries += 1

        if status == "failure":
            raise CheckTimeoutError()

    async def get(
        self, url: str, headers: dict = None, cookies: dict = None
    ) -> httpx.Response:
        curr_retries: int = 0
        status: str = "failure"

        while self.MAXIMUM_RETRIES < self.MAXIMUM_RETRIES and status == "failure":
            try:
                res: httpx.Response = await self._async_client.get(
                    url, headers=headers, cookies=cookies
                )

                status = "success"
                return res
            except httpx.ConnectError, httpx.ConnectTimeout:
                curr_retries += 1
