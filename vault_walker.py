"""
Walks an Obsidian vault or UpNote backup directory and yields
(relative_path_parts, markdown_file_path) tuples.

Folder structure mapping to OneNote:
  vault/                          -> Notebook root
  vault/FolderA/                  -> Section Group "FolderA"
  vault/FolderA/SubFolder/        -> Section Group "SubFolder" (nested)
  vault/FolderA/note.md           -> Page in Section "FolderA"
  vault/FolderA/SubFolder/note.md -> Page in Section "SubFolder"

Notes directly in the vault root go into a special "_Root Notes" section.

Obsidian-specific ignores: .obsidian/, .trash/, templates folders.
UpNote-specific: export is typically a flat zip with folders per notebook.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Iterator

IGNORED_DIRS = {
    ".obsidian", ".trash", ".git", ".stfolder", ".stversions",
    "node_modules", "__pycache__",
}

IGNORED_DIR_PATTERNS = {
    "templates", "template", "_templates",
}

ROOT_SECTION_NAME = "_Root Notes"


@dataclass
class NoteEntry:
    """Represents a single markdown note to import."""
    title: str
    file_path: Path
    # Ordered list of folder names from vault root to the note's parent dir.
    # Empty list means the note is in the vault root.
    folder_path: list[str] = field(default_factory=list)


def walk_vault(vault_path: Path, ignore_templates: bool = True) -> Iterator[NoteEntry]:
    """
    Recursively walk a vault directory and yield NoteEntry for each .md file.
    """
    vault_path = vault_path.resolve()
    yield from _walk_dir(vault_path, vault_path, [], ignore_templates)


def _walk_dir(
    root: Path,
    current: Path,
    folder_path: list[str],
    ignore_templates: bool,
) -> Iterator[NoteEntry]:
    try:
        entries = sorted(current.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    except PermissionError:
        return

    for entry in entries:
        if entry.name.startswith("."):
            continue

        if entry.is_dir():
            dir_name_lower = entry.name.lower()
            if entry.name in IGNORED_DIRS:
                continue
            if ignore_templates and dir_name_lower in IGNORED_DIR_PATTERNS:
                continue
            yield from _walk_dir(root, entry, folder_path + [entry.name], ignore_templates)

        elif entry.is_file() and entry.suffix.lower() in {".md", ".markdown", ".txt"}:
            title = entry.stem  # filename without extension
            yield NoteEntry(
                title=title,
                file_path=entry,
                folder_path=folder_path,
            )


def count_notes(vault_path: Path, ignore_templates: bool = True) -> int:
    """Count total notes in a vault without loading content."""
    return sum(1 for _ in walk_vault(vault_path, ignore_templates))
