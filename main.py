"""
md-to-onenote: Import Obsidian/UpNote markdown vaults into Microsoft OneNote
via the Microsoft Graph API.

Usage:
    python main.py import --vault "C:/path/to/vault" --notebook "My Imported Notes"
    python main.py import --vault "C:/path/to/vault" --notebook "My Notes" --dry-run
    python main.py auth --logout
    python main.py list-notebooks
"""

import sys
import os
import click
from pathlib import Path
from rich.console import Console
from rich.table import Table

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

from auth import get_access_token, clear_token_cache
from graph_client import GraphClient
from importer import run_import

console = Console()

DEFAULT_CLIENT_ID = os.getenv("AZURE_CLIENT_ID", "")


def _get_client(client_id: str) -> GraphClient:
    if not client_id:
        console.print(
            "[red]ERROR:[/red] No Azure App Client ID provided.\n"
            "Set AZURE_CLIENT_ID in a .env file or pass --client-id.\n"
            "See README.md for setup instructions.",
            highlight=False,
        )
        sys.exit(1)
    return GraphClient(lambda: get_access_token(client_id))


@click.group()
def cli():
    """md-to-onenote: Bulk import Markdown notes into Microsoft OneNote."""
    pass


@cli.command("import")
@click.option(
    "--vault",
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Path to your Obsidian vault or UpNote backup folder.",
)
@click.option(
    "--notebook",
    required=True,
    help="Name of the OneNote notebook to import into (created if it doesn't exist).",
)
@click.option(
    "--client-id",
    default=DEFAULT_CLIENT_ID,
    envvar="AZURE_CLIENT_ID",
    help="Azure App Registration Client ID.",
)
@click.option(
    "--skip-existing/--overwrite",
    default=True,
    help="Skip notes that already exist in OneNote (default: skip).",
)
@click.option(
    "--include-templates/--ignore-templates",
    default=False,
    help="Include template folders (default: ignore folders named 'templates').",
)
@click.option(
    "--delay",
    default=1000,
    type=int,
    help="Milliseconds to wait between API calls to avoid throttling (default: 1000).",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Walk the vault and show what would be imported without actually doing it.",
)
def import_cmd(vault, notebook, client_id, skip_existing, include_templates, delay, dry_run):
    """Import a Markdown vault into a OneNote notebook."""
    console.print(f"\n[bold blue]md-to-onenote[/bold blue] — Markdown to OneNote importer\n")

    if not dry_run:
        client = _get_client(client_id)
    else:
        client = None  # Not used in dry run

    stats = run_import(
        vault_path=vault,
        notebook_name=notebook,
        client=client,
        skip_existing=skip_existing,
        ignore_templates=not include_templates,
        delay_ms=delay,
        dry_run=dry_run,
    )
    stats.summary()


@cli.command("list-notebooks")
@click.option(
    "--client-id",
    default=DEFAULT_CLIENT_ID,
    envvar="AZURE_CLIENT_ID",
    help="Azure App Registration Client ID.",
)
def list_notebooks(client_id):
    """List all OneNote notebooks in your account."""
    client = _get_client(client_id)
    notebooks = client.list_notebooks()

    if not notebooks:
        console.print("[yellow]No notebooks found.[/yellow]")
        return

    table = Table(title="Your OneNote Notebooks")
    table.add_column("Name", style="cyan")
    table.add_column("ID", style="dim")
    table.add_column("Last Modified", style="green")

    for nb in notebooks:
        table.add_row(
            nb.get("displayName", ""),
            nb.get("id", ""),
            nb.get("lastModifiedDateTime", ""),
        )

    console.print(table)


@cli.command("auth")
@click.option("--logout", is_flag=True, help="Clear saved authentication tokens.")
@click.option(
    "--client-id",
    default=DEFAULT_CLIENT_ID,
    envvar="AZURE_CLIENT_ID",
    help="Azure App Registration Client ID.",
)
def auth_cmd(logout, client_id):
    """Manage authentication (login / logout)."""
    if logout:
        clear_token_cache()
        return

    console.print("[bold]Testing authentication...[/bold]")
    client = _get_client(client_id)
    notebooks = client.list_notebooks()
    console.print(f"[green]Authenticated successfully![/green] Found {len(notebooks)} notebook(s).")


if __name__ == "__main__":
    cli()
