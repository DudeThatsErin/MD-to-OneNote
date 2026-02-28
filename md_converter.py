"""
Converts Markdown content to OneNote-compatible HTML.
Handles headings, bold/italic, code blocks, tables, links,
blockquotes, images, and horizontal rules.
"""

import re
import base64
import os
from pathlib import Path
import markdown2


def markdown_to_onenote_html(md_content: str, source_file: Path) -> str:
    """
    Convert markdown text to OneNote-compatible HTML.
    source_file is used to resolve relative image paths.
    """
    # Pre-process: strip YAML front matter (Obsidian/UpNote)
    md_content = _strip_front_matter(md_content)

    # Pre-process: convert Obsidian wiki links [[Note]] -> Note
    md_content = _convert_wiki_links(md_content)

    # Pre-process: convert Obsidian callouts > [!NOTE] etc.
    md_content = _convert_obsidian_callouts(md_content)

    # Convert markdown to HTML using markdown2
    html = markdown2.markdown(
        md_content,
        extras=[
            "fenced-code-blocks",
            "tables",
            "strike",
            "task_list",
            "footnotes",
            "header-ids",
            "break-on-newline",
            "smarty-pants",
            "code-friendly",
        ],
    )

    # Post-process: inline local images as base64
    html = _inline_local_images(html, source_file.parent)

    # Post-process: clean up for OneNote compatibility
    html = _clean_for_onenote(html)

    return html


def _strip_front_matter(content: str) -> str:
    """Remove YAML front matter delimited by --- at start of file."""
    stripped = content.lstrip()
    if stripped.startswith("---"):
        end = stripped.find("\n---", 3)
        if end != -1:
            return stripped[end + 4:].lstrip()
    return content


def _convert_wiki_links(content: str) -> str:
    """
    Convert Obsidian wiki links to plain text or markdown links.
    [[Note Name]] -> Note Name
    [[Note Name|Display Text]] -> Display Text
    ![[image.png]] -> handled separately
    """
    # Image embeds ![[file]] - leave as markdown image reference
    content = re.sub(
        r"!\[\[([^\]|]+?)(?:\|[^\]]*?)?\]\]",
        lambda m: f"![{m.group(1)}]({m.group(1)})",
        content,
    )
    # Wiki links with display text [[target|display]] -> display
    content = re.sub(r"\[\[([^\]|]+?)\|([^\]]+?)\]\]", r"\2", content)
    # Plain wiki links [[target]] -> target
    content = re.sub(r"\[\[([^\]]+?)\]\]", r"\1", content)
    return content


def _convert_obsidian_callouts(content: str) -> str:
    """
    Convert Obsidian callout syntax:
    > [!NOTE] Title
    > content
    -> <blockquote><strong>NOTE: Title</strong><br>content</blockquote>
    """
    def replace_callout(match):
        callout_type = match.group(1).upper()
        title = match.group(2).strip() if match.group(2) else ""
        body = match.group(3).strip() if match.group(3) else ""
        # Strip leading "> " from body lines
        body_lines = re.sub(r"^> ?", "", body, flags=re.MULTILINE)
        label = f"{callout_type}: {title}" if title else callout_type
        return f"> **{label}**\n>\n> {body_lines}\n"

    pattern = re.compile(
        r"^> \[!([A-Za-z]+)\](.*?)\n((?:>.*\n?)*)",
        re.MULTILINE,
    )
    return pattern.sub(replace_callout, content)


def _inline_local_images(html: str, base_dir: Path) -> str:
    """
    Find <img src="..."> tags with local file paths and replace with
    base64 data URIs so images show in OneNote.
    """
    def replace_img(match):
        src = match.group(1)
        # Skip URLs and data URIs
        if src.startswith(("http://", "https://", "data:", "//")):
            return match.group(0)

        # Decode URL encoding
        img_path = Path(base_dir) / src.replace("%20", " ")
        if not img_path.exists():
            # Try just the filename
            img_path = base_dir / Path(src).name
        if not img_path.exists():
            return match.group(0)

        try:
            with open(img_path, "rb") as f:
                data = f.read()
            ext = img_path.suffix.lower().lstrip(".")
            mime_map = {
                "jpg": "image/jpeg", "jpeg": "image/jpeg",
                "png": "image/png", "gif": "image/gif",
                "webp": "image/webp", "svg": "image/svg+xml",
            }
            mime = mime_map.get(ext, "image/png")
            b64 = base64.b64encode(data).decode("utf-8")
            return f'<img src="data:{mime};base64,{b64}"'
        except Exception:
            return match.group(0)

    return re.sub(r'<img src="([^"]*)"', replace_img, html)


def _clean_for_onenote(html: str) -> str:
    """
    Clean HTML for OneNote compatibility:
    - OneNote doesn't support all CSS; remove style attrs that break rendering
    - Ensure code blocks use <pre> style OneNote understands
    - Task list checkboxes: convert to text indicators
    """
    # Style code blocks for OneNote (monospace, light background)
    html = re.sub(
        r"<pre><code([^>]*)>",
        '<pre style="font-family: Courier New, monospace; background-color: #f5f5f5; '
        'padding: 10px; border: 1px solid #ddd; overflow-x: auto;"><code\1>',
        html,
    )

    # Style inline code
    html = re.sub(
        r"<code>",
        '<code style="font-family: Courier New, monospace; background-color: #f5f5f5; '
        'padding: 2px 4px; border-radius: 3px;">',
        html,
    )

    # Style blockquotes
    html = re.sub(
        r"<blockquote>",
        '<blockquote style="border-left: 4px solid #ccc; margin-left: 0; '
        'padding-left: 16px; color: #555;">',
        html,
    )

    # Style tables
    html = re.sub(r"<table>", '<table style="border-collapse: collapse; width: 100%;">', html)
    html = re.sub(r"<th>", '<th style="border: 1px solid #ddd; padding: 8px; background-color: #f2f2f2;">', html)
    html = re.sub(r"<td>", '<td style="border: 1px solid #ddd; padding: 8px;">', html)

    # Checked task list items - markdown2 outputs <li class="task-list-item">
    html = re.sub(
        r'<li class="task-list-item"><input[^>]+checked[^>]+/?>',
        "<li>&#9989; ",
        html,
    )
    html = re.sub(
        r'<li class="task-list-item"><input[^>]+/?>',
        "<li>&#9744; ",
        html,
    )

    return html
