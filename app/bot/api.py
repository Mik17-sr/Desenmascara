"""HTTP client from the bot to the API. The bot holds BOT_API_SECRET; the API does all the work."""

import httpx

from app.core.config import settings

TEXT_TIMEOUT = 8.0  # the guide's budget: an answer in less than 8 seconds
IMAGE_TIMEOUT = settings.BOT_TIMEOUT_IMAGEN
VOICE_TIMEOUT = settings.BOT_TIMEOUT_VOZ


class ApiError(Exception):
    def __init__(self, status: int, detail: str):
        super().__init__(detail)
        self.status = status
        self.detail = detail


class Api:
    def __init__(self) -> None:
        self.client = httpx.AsyncClient(
            base_url=settings.API_BASE_URL.rstrip("/") + settings.API_V1_STR,
            headers={"X-Bot-Secret": settings.BOT_API_SECRET},
            timeout=TEXT_TIMEOUT,
        )

    async def post(self, path: str, timeout: float = TEXT_TIMEOUT, **kwargs) -> dict:
        try:
            response = await self.client.post(path, timeout=timeout, **kwargs)
        except httpx.HTTPError as exc:
            raise ApiError(0, "sin conexión") from exc
        return self._json(response)

    async def get(self, path: str) -> dict:
        try:
            response = await self.client.get(path)
        except httpx.HTTPError as exc:
            raise ApiError(0, "sin conexión") from exc
        return self._json(response)

    @staticmethod
    def _json(response: httpx.Response) -> dict:
        if response.status_code >= 400:
            try:
                detail = response.json().get("detail", "")
            except ValueError:
                detail = ""
            raise ApiError(response.status_code, detail if isinstance(detail, str) else "")
        return response.json()

    async def close(self) -> None:
        await self.client.aclose()
