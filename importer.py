"""
Core import orchestrator.
Walks the vault, resolves OneNote structure, and creates pages.
"""

import time
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn

from vault_walker import walk_vault, count_notes, ROOT_SECTION_NAME
from graph_client import GraphClient
from md_converter import markdown_to_onenote_html

console = Console()


class ImportStats:
    def __init__(self):
        self.created = 0
        self.skipped = 0
        self.failed = 0
        self.failed_titles: list[str] = []

    def summary(self):
        console.print(f"\n[bold green]Import Complete![/bold green]")
        console.print(f"  [green]Created:[/green]  {self.created}")
        console.print(f"  [yellow]Skipped:[/yellow]  {self.skipped} (already existed)")
        console.print(f"  [red]Failed:[/red]   {self.failed}")
        if self.failed_titles:
            console.print("\n[red]Failed notes:[/red]")
            for t in self.failed_titles[:20]:
                console.print(f"  - {t}")
            if len(self.failed_titles) > 20:
                console.print(f"  ... and {len(self.failed_titles) - 20} more")


def run_import(
    vault_path: Path,
    notebook_name: str,
    client: GraphClient,
    skip_existing: bool = True,
    ignore_templates: bool = True,
    delay_ms: int = 200,
    dry_run: bool = False,
) -> ImportStats:
    """
    Main import function. Walks vault, maps folders to OneNote structure,
    and creates pages.

    Structure mapping:
      - Notes at vault root            -> Section "_Root Notes" in notebook
      - Notes in 1-level folder        -> Section "FolderName" in notebook
      - Notes in 2+ level folders      -> Section Group for parent(s),
                                          Section for immediate parent
    """
    stats = ImportStats()

    console.print(f"\n[bold]Counting notes in:[/bold] {vault_path}")
    total = count_notes(vault_path, ignore_templates)
    console.print(f"[bold]Found:[/bold] {total} notes")
    console.print(f"[bold]Target notebook:[/bold] {notebook_name}")

    if dry_run:
        console.print("\n[yellow][DRY RUN] No changes will be made to OneNote.[/yellow]\n")

    # Get or create the target notebook
    if not dry_run:
        console.print(f"\nResolving notebook '{notebook_name}'...")
        notebook_id = client.get_or_create_notebook(notebook_name)
        console.print(f"[green]Notebook ready.[/green]")
    else:
        notebook_id = "dry-run-notebook-id"

    delay = delay_ms / 1000.0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    ) as progress:
        task = progress.add_task("Importing notes...", total=total)

        for note in walk_vault(vault_path, ignore_templates):
            progress.update(task, description=f"[cyan]{note.title[:50]}[/cyan]")

            try:
                section_id = _resolve_section(
                    note.folder_path,
                    notebook_id,
                    client,
                    dry_run,
                )

                if not dry_run:
                    # Check for duplicate
                    if skip_existing and client.page_exists(section_id, note.title):
                        stats.skipped += 1
                        progress.advance(task)
                        continue

                    # Read and convert markdown
                    try:
                        raw = note.file_path.read_text(encoding="utf-8", errors="replace")
                    except Exception as e:
                        raise RuntimeError(f"Could not read file: {e}")

                    html_body = markdown_to_onenote_html(raw, note.file_path)

                    # Create page
                    client.create_page(section_id, note.title, html_body)
                    stats.created += 1

                    # Rate limiting - Graph API has throttle limits
                    time.sleep(delay)
                else:
                    folder_display = " / ".join(note.folder_path) if note.folder_path else "(root)"
                    console.log(f"[dim]DRY RUN:[/dim] '{note.title}' -> {folder_display}")
                    stats.created += 1

            except Exception as e:
                stats.failed += 1
                stats.failed_titles.append(note.title)
                console.print(f"\n[red]ERROR[/red] '{note.title}': {e}")

            progress.advance(task)

    return stats


def _resolve_section(
    folder_path: list[str],
    notebook_id: str,
    client: GraphClient,
    dry_run: bool,
) -> str:
    """
    Map a folder path to a OneNote section ID.

    folder_path = []           -> Section "_Root Notes" directly in notebook
    folder_path = ["A"]        -> Section "A" directly in notebook
    folder_path = ["A", "B"]   -> SectionGroup "A" -> Section "B"
    folder_path = ["A","B","C"]-> SectionGroup "A" -> SectionGroup "B" -> Section "C"
    """
    if dry_run:
        return "dry-run-section-id"

    if not folder_path:
        return client.get_or_create_section(ROOT_SECTION_NAME, notebook_id, None)

    if len(folder_path) == 1:
        return client.get_or_create_section(folder_path[0], notebook_id, None)

    # Multiple levels: all but last are section groups, last is the section
    parent_group_id: Optional[str] = None

    for folder_name in folder_path[:-1]:
        parent_group_id = client.get_or_create_section_group(
            folder_name,
            notebook_id,
            parent_group_id,
        )

    section_name = folder_path[-1]
    return client.get_or_create_section(
        section_name,
        notebook_id,
        parent_group_id,
    )
