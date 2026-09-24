#!/usr/bin/env python3
"""Filtra mensajes de excusa de un export Discord JSON."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Aperturas típicas de anuncios de descanso / excusa (tras quitar @everyone).
# Orden: frases más largas primero para claridad; el match usa word-boundary.
EXCUSA_OPENINGS = (
    r"disculpen mi gentesita",
    r"buenas mi gentesita",
    r"bueno mi gentesita",
    r"buenas mi gente",
    r"mi dulce gentesita",
    r"mi gentesita",
    r"mi gente",
)

EXCUSA_PATTERN = re.compile(
    r"^(?:" + "|".join(EXCUSA_OPENINGS) + r")\b",
    re.IGNORECASE,
)


def normalize_opening(content: str) -> str:
    text = (content or "").strip()
    text = re.sub(r"^@everyone\s*", "", text, flags=re.IGNORECASE)
    return text.lstrip()


def is_excusa_message(content: str) -> bool:
    opening = normalize_opening(content)
    return bool(EXCUSA_PATTERN.match(opening))


def load_messages(path: Path) -> list:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "messages" in data:
        return list(data["messages"])
    if isinstance(data, list):
        return data
    raise ValueError("Formato JSON no reconocido (lista o {messages: [...]})")


def slim_message(message: dict) -> dict:
    """Versión legible: texto + meta + top reacciones + adjuntos."""
    reactions = message.get("reactions") or []
    top = []
    for reaction in sorted(reactions, key=lambda r: r.get("count") or 0, reverse=True)[:6]:
        emoji = reaction.get("emoji") or {}
        name = emoji.get("name") or "?"
        top.append({"emoji": name, "count": reaction.get("count")})

    attachments = []
    for att in message.get("attachments") or []:
        attachments.append(
            {
                "id": att.get("id"),
                "filename": att.get("filename"),
                "size": att.get("size"),
                "url": att.get("url"),
                "content_type": att.get("content_type"),
                "title": att.get("title"),
            }
        )

    author = message.get("author") or {}
    return {
        "id": message.get("id"),
        "channel_id": message.get("channel_id"),
        "timestamp": message.get("timestamp"),
        "content": message.get("content") or "",
        "author": {
            "id": author.get("id"),
            "username": author.get("username"),
            "global_name": author.get("global_name"),
        },
        "mention_everyone": message.get("mention_everyone", False),
        "attachments": attachments,
        "top_reactions": top,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Filtra mensajes de excusa (aperturas mi gente / mi gentesita, etc.)."
    )
    parser.add_argument("entrada", type=Path, help="JSON crudo (lista o {messages})")
    parser.add_argument("salida", type=Path, help="JSON de salida")
    parser.add_argument(
        "--full",
        action="store_true",
        help="Conservar el objeto de mensaje completo (sin slim).",
    )
    args = parser.parse_args()

    try:
        messages = load_messages(args.entrada)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Error leyendo entrada: {exc}", file=sys.stderr)
        return 1

    matched = [m for m in messages if is_excusa_message(m.get("content") or "")]
    matched.sort(key=lambda m: m.get("timestamp") or "")
    out_messages = matched if args.full else [slim_message(m) for m in matched]

    openings_human = [
        "mi gentesita",
        "mi dulce gentesita",
        "mi gente",
        "buenas mi gentesita",
        "buenas mi gente",
        "bueno mi gentesita",
        "disculpen mi gentesita",
    ]
    payload = {
        "filter": {
            "openings": openings_human,
            "rule": (
                "Tras quitar @everyone opcional, el content empieza con una de las "
                "aperturas de excusa (límite de palabra; sin distinguir mayúsculas)."
            ),
            "match_count": len(out_messages),
            "source_count": len(messages),
            "source": str(args.entrada),
            "channel_id": (out_messages[0].get("channel_id") if out_messages else None),
        },
        "messages": out_messages,
    }

    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"OK: {len(out_messages)}/{len(messages)} → {args.salida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
