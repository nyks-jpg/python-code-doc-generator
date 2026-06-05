from pathlib import Path

from main import collect_functions, discover_python_files


def test_collect_functions_extracts_metadata(tmp_path: Path) -> None:
    source = tmp_path / "sample.py"
    source.write_text(
        '''
class InvoiceService:
    def create_invoice(self, customer_id: str, amount: float = 0.0) -> str:
        """Create an invoice for the customer."""
        if amount < 0:
            raise ValueError("amount must be positive")
        return customer_id
'''.strip(),
        encoding="utf-8",
    )

    docs = collect_functions(source, include_private=False, language="en")

    assert len(docs) == 1
    doc = docs[0]
    assert doc.qualified_name == "InvoiceService.create_invoice"
    assert doc.kind == "method"
    assert doc.returns == "str"
    assert "ValueError" in doc.raises
    assert "customer_id: str" in doc.signature
    assert "amount: float = 0.0" in doc.signature


def test_private_functions_are_excluded_by_default(tmp_path: Path) -> None:
    source = tmp_path / "sample.py"
    source.write_text(
        '''
def public_function() -> int:
    return 1

def _private_function() -> int:
    return 2
'''.strip(),
        encoding="utf-8",
    )

    public_docs = collect_functions(source, include_private=False, language="en")
    all_docs = collect_functions(source, include_private=True, language="en")

    assert [doc.name for doc in public_docs] == ["public_function"]
    assert [doc.name for doc in all_docs] == ["public_function", "_private_function"]


def test_discover_python_files_respects_non_recursive_mode(tmp_path: Path) -> None:
    root_file = tmp_path / "root.py"
    nested_dir = tmp_path / "nested"
    nested_dir.mkdir()
    nested_file = nested_dir / "child.py"
    root_file.write_text("def root():\n    return None\n", encoding="utf-8")
    nested_file.write_text("def child():\n    return None\n", encoding="utf-8")

    top_level = discover_python_files(tmp_path, recursive=False)
    recursive = discover_python_files(tmp_path, recursive=True)

    assert top_level == [root_file.resolve()]
    assert recursive == [nested_file.resolve(), root_file.resolve()]
