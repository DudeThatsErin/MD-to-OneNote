"""Tests for main.py CLI (run with: pytest test_main.py -v)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from click.testing import CliRunner

from main import cli


def _vault_with_note(tmp_path):
    (tmp_path / "note.md").write_text("# hello\n", encoding="utf-8")
    return tmp_path


def test_negative_delay_rejected(tmp_path):
    """--delay=-5 must fail parsing instead of being silently accepted."""
    vault = _vault_with_note(tmp_path)
    result = CliRunner().invoke(
        cli,
        ["import", "--vault", str(vault), "--notebook", "N", "--dry-run", "--delay=-5"],
    )
    assert result.exit_code == 2
    assert "--delay" in result.output


def test_dry_run_accepts_default_delay(tmp_path):
    """A normal dry run still exits 0."""
    vault = _vault_with_note(tmp_path)
    result = CliRunner().invoke(
        cli, ["import", "--vault", str(vault), "--notebook", "N", "--dry-run"]
    )
    assert result.exit_code == 0
