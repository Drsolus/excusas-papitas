"""Serialización y escritura del export."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def safe_name(value: str, fallback: str = "item") -> str:
    cleaned = re.sub(r"[^\w.\-]+", "_", value, flags=re.UNICODE).strip("._")
    return cleaned[:120] or fallback


def author_label(author: dict[str, Any] | None) -> str:
    if not author:
        return "unknown"
    username = author.get("username") or "user"
    discriminator = author.get("discriminator")
    user_id = author.get("id", "")
    if discriminator and discriminator != "0":
        return f"{username}#{discriminator} ({user_id})"
    return f"{username} ({user_id})"


def format_timestamp(iso: str | None) -> str:
    if not iso:
        return ""
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    except ValueError:
        return iso


def normalize_message(message: dict[str, Any], media_paths: list[str]) -> dict[str, Any]:
    return {
        "id": message.get("id"),
        "type": message.get("type"),
        "timestamp": message.get("timestamp"),
        "edited_timestamp": message.get("edited_timestamp"),
        "content": message.get("content") or "",
        "author": {
            "id": (message.get("author") or {}).get("id"),
            "username": (message.get("author") or {}).get("username"),
            "global_name": (message.get("author") or {}).get("global_name"),
            "bot": (message.get("author") or {}).get("bot", False),
        },
        "mentions": [
            {"id": m.get("id"), "username": m.get("username")}
            for m in message.get("mentions") or []
        ],
        "mention_roles": message.get("mention_roles") or [],
        "mention_everyone": message.get("mention_everyone", False),
        "pinned": message.get("pinned", False),
        "tts": message.get("tts", False),
        "flags": message.get("flags"),
        "reactions": [
            {
                "emoji": (r.get("emoji") or {}).get("name"),
                "emoji_id": (r.get("emoji") or {}).get("id"),
                "count": r.get("count"),
            }
            for r in message.get("reactions") or []
        ],
        "embeds": message.get("embeds") or [],
        "stickers": message.get("sticker_items") or message.get("stickers") or [],
        "referenced_message_id": (message.get("referenced_message") or {}).get("id")
        if message.get("referenced_message")
        else (message.get("message_reference") or {}).get("message_id"),
        "attachments": [
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
                "local_path": None,
            }
            for a in message.get("attachments") or []
        ],
        "local_media": media_paths,
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_markdown(
    path: Path,
    *,
    channel: dict[str, Any],
    guild: dict[str, Any] | None,
    messages: list[dict[str, Any]],
) -> None:
    channel_name = channel.get("name") or channel.get("id")
    guild_name = (guild or {}).get("name") or "DM / desconocido"
    lines = [
        f"# Export: #{channel_name}",
        "",
        f"- **Servidor:** {guild_name}",
        f"- **Canal ID:** `{channel.get('id')}`",
        f"- **Tipo:** {channel.get('type')}",
        f"- **Tema:** {channel.get('topic') or '—'}",
        f"- **Mensajes:** {len(messages)}",
        f"- **Exportado:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "",
        "---",
        "",
    ]

    # Chronological (oldest first) for reading
    for msg in sorted(messages, key=lambda m: m.get("timestamp") or ""):
        author = author_label(msg.get("author"))
        ts = format_timestamp(msg.get("timestamp"))
        lines.append(f"### {author} — {ts}")
        lines.append(f"`id:{msg.get('id')}`")
        lines.append("")
        content = (msg.get("content") or "").strip()
        if content:
            lines.append(content)
            lines.append("")
        for emb in msg.get("embeds") or []:
            title = emb.get("title") or emb.get("author", {}).get("name") or "embed"
            desc = emb.get("description") or ""
            lines.append(f"> **Embed:** {title}")
            if desc:
                for part in desc.splitlines() or [""]:
                    lines.append(f"> {part}")
            lines.append("")
        for media in msg.get("local_media") or []:
            lines.append(f"![]({media})")
            lines.append("")
        for att in msg.get("attachments") or []:
            local = att.get("local_path")
            name = att.get("filename") or "archivo"
            if local:
                lines.append(f"- Adjunto: [{name}]({local})")
            elif att.get("url"):
                lines.append(f"- Adjunto: [{name}]({att['url']})")
        reactions = msg.get("reactions") or []
        if reactions:
            bits = [
                f"{r.get('emoji') or '?'}×{r.get('count')}" for r in reactions
            ]
            lines.append("Reacciones: " + " · ".join(bits))
            lines.append("")
        lines.append("---")
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
