"""Cliente HTTP para la API REST de Discord."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

API_BASE = "https://discord.com/api/v10"
USER_AGENT = "DiscordChannelExporter (local-archive; +https://github.com/local)"


class DiscordAPIError(Exception):
    def __init__(self, status: int, message: str) -> None:
        self.status = status
        super().__init__(f"Discord API {status}: {message}")


class DiscordClient:
    def __init__(self, token: str, *, timeout: float = 30.0) -> None:
        self._token = token.strip()
        self._client = httpx.AsyncClient(
            base_url=API_BASE,
            headers={
                "Authorization": f"Bot {self._token}",
                "User-Agent": USER_AGENT,
            },
            timeout=timeout,
            follow_redirects=True,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> DiscordClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> Any:
        while True:
            response = await self._client.request(method, path, params=params)
            if response.status_code == 429:
                retry_after = float(response.json().get("retry_after", 1))
                await asyncio.sleep(retry_after + 0.1)
                continue
            if response.status_code >= 400:
                try:
                    detail = response.json()
                    message = detail.get("message", response.text)
                except Exception:
                    message = response.text
                raise DiscordAPIError(response.status_code, message)
            if response.status_code == 204:
                return None
            return response.json()

    async def get_channel(self, channel_id: str) -> dict[str, Any]:
        return await self._request("GET", f"/channels/{channel_id}")

    async def get_guild(self, guild_id: str) -> dict[str, Any]:
        return await self._request("GET", f"/guilds/{guild_id}")

    async def get_messages(
        self,
        channel_id: str,
        *,
        limit: int = 100,
        before: str | None = None,
        after: str | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"limit": min(limit, 100)}
        if before:
            params["before"] = before
        if after:
            params["after"] = after
        data = await self._request(
            "GET", f"/channels/{channel_id}/messages", params=params
        )
        return list(data)

    async def iter_all_messages(
        self,
        channel_id: str,
        *,
        on_batch: Any | None = None,
    ):
        """Recorre el historial completo, del más reciente al más antiguo."""
        before: str | None = None
        total = 0
        while True:
            batch = await self.get_messages(channel_id, limit=100, before=before)
            if not batch:
                break
            total += len(batch)
            if on_batch:
                on_batch(total, batch)
            for message in batch:
                yield message
            before = batch[-1]["id"]
            # Respeto suave al rate limit global
            await asyncio.sleep(0.35)

    async def download_bytes(self, url: str) -> bytes:
        """Descarga un adjunto/CDN. Usa el mismo cliente con auth por si hace falta."""
        # URLs de CDN suelen ser públicas con query signed; no forzar base Discord API
        async with httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT},
            timeout=60.0,
            follow_redirects=True,
        ) as plain:
            while True:
                response = await plain.get(url)
                if response.status_code == 429:
                    retry_after = float(response.headers.get("Retry-After", "1"))
                    await asyncio.sleep(retry_after + 0.1)
                    continue
                response.raise_for_status()
                return response.content
