"""CLI: discord-export."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv
from rich.console import Console

from exporter import __version__
from exporter.export import run_export, write_demo_export

app = typer.Typer(
    add_completion=False,
    help="Exporta todo el contenido de un canal de Discord (mensajes + adjuntos).",
    no_args_is_help=True,
)
console = Console()


def _load_env() -> None:
    load_dotenv(Path.cwd() / ".env")
    load_dotenv()


@app.callback()
def main() -> None:
    """Discord Channel Exporter."""
    _load_env()


@app.command("export")
def export_cmd(
    channel_id: Optional[str] = typer.Argument(
        None,
        help="ID del canal. Si se omite, usa DISCORD_CHANNEL_ID del .env",
    ),
    token: Optional[str] = typer.Option(
        None,
        "--token",
        "-t",
        envvar="DISCORD_BOT_TOKEN",
        help="Token del bot (o DISCORD_BOT_TOKEN).",
    ),
    output: Path = typer.Option(
        Path("exports"),
        "--output",
        "-o",
        help="Carpeta base de salida.",
    ),
    skip_media: bool = typer.Option(
        False,
        "--skip-media",
        help="Solo guarda metadatos/texto, sin descargar imágenes/archivos.",
    ),
) -> None:
    """Descarga el historial completo de un canal."""
    resolved_channel = channel_id or os.getenv("DISCORD_CHANNEL_ID")
    resolved_token = token or os.getenv("DISCORD_BOT_TOKEN")

    if not resolved_token:
        console.print(
            "[red]Falta el token del bot.[/red] "
            "Copia .env.example → .env y pega DISCORD_BOT_TOKEN."
        )
        raise typer.Exit(1)
    if not resolved_channel:
        console.print(
            "[red]Falta el ID del canal.[/red] "
            "Pásalo como argumento o define DISCORD_CHANNEL_ID en .env."
        )
        raise typer.Exit(1)
    if resolved_token.startswith("tu_token") or "aqui" in resolved_token.lower():
        console.print(
            "[red]El token de .env sigue siendo el placeholder.[/red] "
            "Sustitúyelo por el token real del bot."
        )
        raise typer.Exit(1)

    out = output / f"channel_{resolved_channel}"
    run_export(resolved_token, resolved_channel, out, skip_media=skip_media)


@app.command("demo")
def demo_cmd(
    output: Path = typer.Option(
        Path("exports/demo"),
        "--output",
        "-o",
        help="Carpeta de salida del demo.",
    ),
) -> None:
    """Genera un export de ejemplo sin conectar a Discord."""
    write_demo_export(output)


@app.command("version")
def version_cmd() -> None:
    """Muestra la versión."""
    console.print(__version__)


if __name__ == "__main__":
    app()
