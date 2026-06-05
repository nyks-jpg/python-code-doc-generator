import json
from pathlib import Path

from main import calculate_coverage, collect_functions, format_json, format_markdown


def test_markdown_output_contains_function_sections(tmp_path: Path) -> None:
    source = tmp_path / "calculator.py"
    source.write_text(
        '''
def add(left: int, right: int) -> int:
    """Add two numbers."""
    return left + right
'''.strip(),
        encoding="utf-8",
    )
    docs = collect_functions(source, include_private=False, language="en")

    output = format_markdown(docs, language="en")

    assert "# Python Code Documentation" in output
    assert "### `add`" in output
    assert "- Signature: `def add(left: int, right: int) -> int`" in output
    assert "- Returns: `int`" in output


def test_json_output_is_machine_readable(tmp_path: Path) -> None:
    source = tmp_path / "calculator.py"
    source.write_text(
        '''
def multiply(left: int, right: int) -> int:
    return left * right
'''.strip(),
        encoding="utf-8",
    )
    docs = collect_functions(source, include_private=False, language="en")

    payload = json.loads(format_json(docs))

    assert payload[0]["name"] == "multiply"
    assert payload[0]["qualified_name"] == "multiply"
    assert payload[0]["returns"] == "int"
    assert payload[0]["parameters"][0]["name"] == "left"


def test_coverage_summary_counts_docstrings(tmp_path: Path) -> None:
    source = tmp_path / "coverage_sample.py"
    source.write_text(
        '''
def documented() -> str:
    """Return a documented value."""
    return "ok"

def undocumented() -> str:
    return "missing"
'''.strip(),
        encoding="utf-8",
    )
    docs = collect_functions(source, include_private=False, language="en")

    summary = calculate_coverage(docs)

    assert summary.percentage == 50
    assert summary.total_functions == 2
    assert summary.documented_functions == 1
    assert summary.undocumented_functions == 1


def test_markdown_output_can_include_coverage_summary(tmp_path: Path) -> None:
    source = tmp_path / "coverage_sample.py"
    source.write_text(
        '''
def documented() -> str:
    """Return a documented value."""
    return "ok"

def undocumented() -> str:
    return "missing"
'''.strip(),
        encoding="utf-8",
    )
    docs = collect_functions(source, include_private=False, language="en")
    summary = calculate_coverage(docs)

    output = format_markdown(docs, language="en", coverage=summary)

    assert "## Documentation Coverage" in output
    assert "Documentation Coverage: 50%" in output
    assert "Undocumented Functions: 1" in output


def test_json_output_can_include_coverage_summary(tmp_path: Path) -> None:
    source = tmp_path / "coverage_sample.py"
    source.write_text(
        '''
def documented() -> str:
    """Return a documented value."""
    return "ok"

def undocumented() -> str:
    return "missing"
'''.strip(),
        encoding="utf-8",
    )
    docs = collect_functions(source, include_private=False, language="en")
    summary = calculate_coverage(docs)

    payload = json.loads(format_json(docs, coverage=summary))

    assert payload["coverage"] == {
        "percentage": 50,
        "total_functions": 2,
        "documented_functions": 1,
        "undocumented_functions": 1,
    }
    assert payload["functions"][0]["name"] == "documented"
