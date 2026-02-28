"""
Microsoft Graph API client for OneNote operations.
Handles notebooks, section groups, sections, and pages with rate limiting.
"""

import time
import sys
import requests
from typing import Optional

GRAPH_BASE = "https://graph.microsoft.com/v1.0/me/onenote"


class GraphClient:
    def __init__(self, token_getter):
        """
        token_getter: a callable that returns a fresh access token string.
        Called once per request batch; re-called automatically on 401.
        """
        self._token_getter = token_getter
        self.session = requests.Session()
        self._apply_token()
        self._notebook_cache: dict[str, str] = {}
        self._section_group_cache: dict[str, str] = {}
        self._section_cache: dict[str, str] = {}

    def _apply_token(self):
        token = self._token_getter()
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make a Graph API request with retry on throttle (429), timeouts, and token expiry."""
        for attempt in range(8):
            resp = self.session.request(method, url, timeout=60, **kwargs)
            if resp.status_code == 429:
                # Use Retry-After header if present, otherwise use exponential backoff
                retry_after = resp.headers.get("Retry-After")
                if retry_after is not None:
                    wait = int(retry_after)
                else:
                    wait = min(30 * (attempt + 1), 300)
                print(f"\n[throttled] Rate limited. Waiting {wait}s before retry {attempt + 1}/8...", file=sys.stderr)
                time.sleep(wait)
                continue
            if resp.status_code in (500, 503, 504):
                wait = 10 * (attempt + 1)
                print(f"\n[server error {resp.status_code}] Waiting {wait}s before retry {attempt + 1}/8...", file=sys.stderr)
                time.sleep(wait)
                continue
            if resp.status_code == 401:
                # Token expired — refresh and retry once
                self._apply_token()
                resp = self.session.request(method, url, timeout=60, **kwargs)
            return resp
        print(f"\n[warning] All retries exhausted, returning last response ({resp.status_code})", file=sys.stderr)
        return resp  # return last response even if still failing

    # -------------------------------------------------------------------------
    # Notebooks
    # -------------------------------------------------------------------------

    def list_notebooks(self) -> list[dict]:
        resp = self._request("GET", f"{GRAPH_BASE}/notebooks")
        resp.raise_for_status()
        return resp.json().get("value", [])

    def get_or_create_notebook(self, name: str) -> str:
        """Return notebook ID, creating if it doesn't exist."""
        if name in self._notebook_cache:
            return self._notebook_cache[name]

        for nb in self.list_notebooks():
            if nb["displayName"].lower() == name.lower():
                self._notebook_cache[name] = nb["id"]
                return nb["id"]

        resp = self._request(
            "POST",
            f"{GRAPH_BASE}/notebooks",
            json={"displayName": name},
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        nb_id = resp.json()["id"]
        self._notebook_cache[name] = nb_id
        return nb_id

    # -------------------------------------------------------------------------
    # Section Groups
    # -------------------------------------------------------------------------

    def list_section_groups(self, notebook_id: str) -> list[dict]:
        resp = self._request("GET", f"{GRAPH_BASE}/notebooks/{notebook_id}/sectionGroups")
        resp.raise_for_status()
        return resp.json().get("value", [])

    def list_nested_section_groups(self, parent_group_id: str) -> list[dict]:
        resp = self._request("GET", f"{GRAPH_BASE}/sectionGroups/{parent_group_id}/sectionGroups")
        resp.raise_for_status()
        return resp.json().get("value", [])

    def get_or_create_section_group(
        self,
        name: str,
        notebook_id: str,
        parent_group_id: Optional[str] = None,
    ) -> str:
        """Return section group ID, creating if needed. Supports nesting."""
        cache_key = f"{parent_group_id or notebook_id}::{name}"
        if cache_key in self._section_group_cache:
            return self._section_group_cache[cache_key]

        if parent_group_id:
            existing = self.list_nested_section_groups(parent_group_id)
            create_url = f"{GRAPH_BASE}/sectionGroups/{parent_group_id}/sectionGroups"
        else:
            existing = self.list_section_groups(notebook_id)
            create_url = f"{GRAPH_BASE}/notebooks/{notebook_id}/sectionGroups"

        for sg in existing:
            if sg["displayName"].lower() == name.lower():
                self._section_group_cache[cache_key] = sg["id"]
                return sg["id"]

        resp = self._request(
            "POST",
            create_url,
            json={"displayName": name},
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        sg_id = resp.json()["id"]
        self._section_group_cache[cache_key] = sg_id
        return sg_id

    # -------------------------------------------------------------------------
    # Sections
    # -------------------------------------------------------------------------

    def list_sections_in_notebook(self, notebook_id: str) -> list[dict]:
        resp = self._request("GET", f"{GRAPH_BASE}/notebooks/{notebook_id}/sections")
        resp.raise_for_status()
        return resp.json().get("value", [])

    def list_sections_in_group(self, group_id: str) -> list[dict]:
        resp = self._request("GET", f"{GRAPH_BASE}/sectionGroups/{group_id}/sections")
        resp.raise_for_status()
        return resp.json().get("value", [])

    def get_or_create_section(
        self,
        name: str,
        notebook_id: str,
        parent_group_id: Optional[str] = None,
    ) -> str:
        """Return section ID, creating if needed."""
        cache_key = f"{parent_group_id or notebook_id}::{name}"
        if cache_key in self._section_cache:
            return self._section_cache[cache_key]

        if parent_group_id:
            existing = self.list_sections_in_group(parent_group_id)
            create_url = f"{GRAPH_BASE}/sectionGroups/{parent_group_id}/sections"
        else:
            existing = self.list_sections_in_notebook(notebook_id)
            create_url = f"{GRAPH_BASE}/notebooks/{notebook_id}/sections"

        for sec in existing:
            if sec["displayName"].lower() == name.lower():
                self._section_cache[cache_key] = sec["id"]
                return sec["id"]

        resp = self._request(
            "POST",
            create_url,
            json={"displayName": name},
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        sec_id = resp.json()["id"]
        self._section_cache[cache_key] = sec_id
        return sec_id

    # -------------------------------------------------------------------------
    # Pages
    # -------------------------------------------------------------------------

    def create_page(self, section_id: str, title: str, html_body: str) -> dict:
        """Create a OneNote page in the given section."""
        page_html = f"""<!DOCTYPE html>
<html>
<head>
  <title>{_escape_html(title)}</title>
</head>
<body>
{html_body}
</body>
</html>"""

        resp = self._request(
            "POST",
            f"{GRAPH_BASE}/sections/{section_id}/pages",
            data=page_html.encode("utf-8"),
            headers={"Content-Type": "application/xhtml+xml"},
        )
        if not resp.ok:
            raise RuntimeError(
                f"Failed to create page '{title}': {resp.status_code} {resp.text[:300]}"
            )
        return resp.json()

    def page_exists(self, section_id: str, title: str) -> bool:
        """Check if a page with this title already exists in the section."""
        resp = self._request(
            "GET",
            f"{GRAPH_BASE}/sections/{section_id}/pages",
            params={"$filter": f"title eq '{title.replace(chr(39), chr(39)+chr(39))}'", "$select": "id,title"},
        )
        if not resp.ok:
            return False
        return len(resp.json().get("value", [])) > 0


def _escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
