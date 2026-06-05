import json
from pathlib import Path

from main import collect_functions, format_json, format_markdown


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
