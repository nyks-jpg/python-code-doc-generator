import json
import subprocess
import sys
from pathlib import Path

from main import run


def test_cli_writes_markdown_output(tmp_path: Path) -> None:
    source = tmp_path / "sample.py"
    output = tmp_path / "docs.md"
    source.write_text(
        '''
def greet(name: str) -> str:
    return f"Hello, {name}"
'''.strip(),
        encoding="utf-8",
    )

    exit_code = run([str(source), "--language", "en", "--output", str(output)])

    assert exit_code == 0
    assert "### `greet`" in output.read_text(encoding="utf-8")


def test_cli_json_flag_writes_json_output(tmp_path: Path) -> None:
    source = tmp_path / "sample.py"
    output = tmp_path / "docs.json"
    source.write_text("def greet(name: str) -> str:\n    return name\n", encoding="utf-8")

    exit_code = run([str(source), "--format", "json", "--output", str(output)])

    assert exit_code == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload[0]["name"] == "greet"


def test_cli_fail_on_empty_returns_non_zero(tmp_path: Path) -> None:
    source = tmp_path / "empty.py"
    source.write_text("VALUE = 1\n", encoding="utf-8")

    exit_code = run([str(source), "--fail-on-empty"])

    assert exit_code == 3


def test_console_version_entrypoint_after_install() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "main", "--version"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Python Code Doc-Generator 0.1.0" in result.stdout
