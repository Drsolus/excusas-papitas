"""Orquestación del export de un canal."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from exporter.api import DiscordClient, DiscordAPIError
from exporter.formatters import normalize_message, safe_name, write_json, write_markdown

console = Console()


async def download_attachments(
    client: DiscordClient,
    messages: list[dict[str, Any]],
    media_dir: Path,
    *,
    skip_media: bool = False,
) -> list[dict[str, Any]]:
    media_dir.mkdir(parents=True, exist_ok=True)
    normalized: list[dict[str, Any]] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        total_atts = sum(len(m.get("attachments") or []) for m in messages)
        task = progress.add_task("Descargando adjuntos…", total=max(total_atts, 1))
        if skip_media or total_atts == 0:
            progress.update(task, completed=max(total_atts, 1))

        for message in messages:
            local_paths: list[str] = []
            atts = message.get("attachments") or []
            saved_atts = []
            for index, att in enumerate(atts):
                filename = att.get("filename") or f"file_{att.get('id')}"
                msg_id = message.get("id", "msg")
                target_name = safe_name(f"{msg_id}_{index}_{filename}")
                target = media_dir / target_name
                relative = f"media/{target_name}"
                entry = dict(att)
                if skip_media:
                    entry["local_path"] = None
                    saved_atts.append(entry)
                    progress.advance(task)
                    continue
                url = att.get("url") or att.get("proxy_url")
                if not url:
                    entry["local_path"] = None
                    saved_atts.append(entry)
                    progress.advance(task)
                    continue
                try:
                    if not target.exists():
                        data = await client.download_bytes(url)
                        target.write_bytes(data)
                    entry["local_path"] = relative
                    local_paths.append(relative)
                except Exception as exc:  # noqa: BLE001 — continuar con el resto
                    console.print(
                        f"[yellow]No se pudo descargar {filename}: {exc}[/yellow]"
                    )
                    entry["local_path"] = None
                    entry["download_error"] = str(exc)
                saved_atts.append(entry)
                progress.advance(task)

            # Spoiler / CDN images sometimes only in embeds
            for emb in message.get("embeds") or []:
                image = emb.get("image") or emb.get("thumbnail") or {}
                url = image.get("url") or image.get("proxy_url")
                if not url or skip_media:
                    continue
                # Evitar duplicar si ya es un attachment
                if any(url == (a.get("url") or a.get("proxy_url")) for a in atts):
                    continue
                emb_name = safe_name(
                    f"{message.get('id')}_embed_{Path(url.split('?')[0]).name}"
                )
                if "." not in emb_name:
                    emb_name += ".jpg"
                target = media_dir / emb_name
                relative = f"media/{emb_name}"
                try:
                    if not target.exists():
                        data = await client.download_bytes(url)
                        target.write_bytes(data)
                    local_paths.append(relative)
                except Exception as exc:  # noqa: BLE001
                    console.print(
                        f"[yellow]No se pudo descargar embed media: {exc}[/yellow]"
                    )

            norm = normalize_message(message, local_paths)
            norm["attachments"] = [
                {
                    "id": a.get("id"),
                    "filename": a.get("filename"),
                    "url": a.get("url"),
                    "proxy_url": a.get("proxy_url"),
                    "size": a.get("size"),
                    "content_type": a.get("content_type"),
                    "width": a.get("width"),
                    "height": a.get("height"),
                    "description": a.get("description"),
                    "local_path": a.get("local_path"),
                    **(
                        {"download_error": a["download_error"]}
                        if a.get("download_error")
                        else {}
                    ),
                }
                for a in saved_atts
            ]
            normalized.append(norm)

    return normalized


async def export_channel(
    token: str,
    channel_id: str,
    output_dir: Path,
    *,
    skip_media: bool = False,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    media_dir = output_dir / "media"

    async with DiscordClient(token) as client:
        console.print("[bold]Conectando con Discord…[/bold]")
        try:
            channel = await client.get_channel(channel_id)
        except DiscordAPIError as exc:
            if exc.status == 401:
                raise SystemExit(
                    "Token inválido. Revisa DISCORD_BOT_TOKEN en .env"
                ) from exc
            if exc.status == 403:
                raise SystemExit(
                    "El bot no tiene permiso para ver este canal.\n"
                    "Invítalo con permisos: Ver canal + Leer historial de mensajes."
                ) from exc
            if exc.status == 404:
                raise SystemExit(
                    "Canal no encontrado. ¿ID correcto? ¿El bot está en el servidor?"
                ) from exc
            raise

        guild = None
        guild_id = channel.get("guild_id")
        if guild_id:
            try:
                guild = await client.get_guild(guild_id)
            except DiscordAPIError:
                guild = {"id": guild_id, "name": None}

        channel_name = channel.get("name") or channel_id
        console.print(
            f"Canal: [cyan]#{channel_name}[/cyan] "
            f"({(guild or {}).get('name') or 'sin servidor'})"
        )

        raw_messages: list[dict[str, Any]] = []
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Leyendo mensajes…", total=None)

            def on_batch(total: int, _batch: list) -> None:
                progress.update(task, description=f"Leyendo mensajes… ({total})")

            async for message in client.iter_all_messages(
                channel_id, on_batch=on_batch
            ):
                raw_messages.append(message)

        console.print(f"Mensajes obtenidos: [green]{len(raw_messages)}[/green]")

        # Guardar crudo por si algo falla al formatear
        write_json(output_dir / "messages.raw.json", raw_messages)

        normalized = await download_attachments(
            client, raw_messages, media_dir, skip_media=skip_media
        )

        # Orden cronológico
        normalized.sort(key=lambda m: m.get("timestamp") or "")

        meta = {
            "exporter": "discord-channel-exporter",
            "channel": {
                "id": channel.get("id"),
                "name": channel.get("name"),
                "type": channel.get("type"),
                "topic": channel.get("topic"),
                "nsfw": channel.get("nsfw"),
                "parent_id": channel.get("parent_id"),
            },
            "guild": guild,
            "message_count": len(normalized),
            "attachment_count": sum(len(m.get("attachments") or []) for m in normalized),
        }

        write_json(output_dir / "meta.json", meta)
        write_json(output_dir / "messages.json", normalized)
        write_markdown(
            output_dir / "channel.md",
            channel=channel,
            guild=guild,
            messages=normalized,
        )

        console.print(f"[bold green]Listo.[/bold green] Export en: {output_dir.resolve()}")
        console.print(
            "Archivos: meta.json · messages.json · channel.md · media/"
        )
        return output_dir


def run_export(
    token: str,
    channel_id: str,
    output_dir: Path,
    *,
    skip_media: bool = False,
) -> Path:
    return asyncio.run(
        export_channel(token, channel_id, output_dir, skip_media=skip_media)
    )


def write_demo_export(output_dir: Path) -> Path:
    """Genera un export de ejemplo sin token (para probar el flujo)."""
    from datetime import datetime, timezone

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "media").mkdir(exist_ok=True)
    sample_png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f"
        b"\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    media_file = output_dir / "media" / "demo_attachment.png"
    media_file.write_bytes(sample_png)

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    channel = {
        "id": "000000000000000000",
        "name": "solo-papitas",
        "type": 5,
        "topic": "Canal de ejemplo (modo demo)",
    }
    guild = {"id": "111", "name": "Servidor de ejemplo"}
    messages = [
        {
            "id": "1",
            "type": 0,
            "timestamp": now,
            "edited_timestamp": None,
            "content": "@everyone Buenas mi gentesita — mensaje de ejemplo del export demo.",
            "author": {
                "id": "222",
                "username": "Papita",
                "global_name": "Papita",
                "bot": False,
            },
            "mentions": [],
            "mention_roles": [],
            "mention_everyone": True,
            "pinned": False,
            "tts": False,
            "flags": 0,
            "reactions": [{"emoji": "🟡", "emoji_id": None, "count": 3}],
            "embeds": [],
            "stickers": [],
            "referenced_message_id": None,
            "attachments": [
                {
                    "id": "att1",
                    "filename": "demo_attachment.png",
                    "url": None,
                    "proxy_url": None,
                    "size": len(sample_png),
                    "content_type": "image/png",
                    "width": 1,
                    "height": 1,
                    "description": None,
                    "local_path": "media/demo_attachment.png",
                }
            ],
            "local_media": ["media/demo_attachment.png"],
        }
    ]
    write_json(
        output_dir / "meta.json",
        {
            "exporter": "discord-channel-exporter",
            "demo": True,
            "channel": channel,
            "guild": guild,
            "message_count": 1,
            "attachment_count": 1,
        },
    )
    write_json(output_dir / "messages.json", messages)
    write_markdown(
        output_dir / "channel.md", channel=channel, guild=guild, messages=messages
    )
    console.print(f"[bold green]Demo listo.[/bold green] {output_dir.resolve()}")
    return output_dir
