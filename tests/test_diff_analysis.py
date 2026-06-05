from pathlib import Path

from main import (
    calculate_diff_analysis,
    collect_functions,
    parse_changed_line_ranges,
)


def test_parse_changed_line_ranges_reads_python_hunks() -> None:
    diff_text = """
diff --git a/sample.py b/sample.py
index 1111111..2222222 100644
--- a/sample.py
+++ b/sample.py
@@ -2,0 +3,2 @@
+def added():
+    return True
@@ -10 +12 @@
-old_value = 1
+new_value = 2
""".strip()

    ranges = parse_changed_line_ranges(diff_text)

    assert ranges == {"sample.py": [(3, 4), (12, 12)]}


def test_diff_analysis_reports_changed_missing_docstrings(tmp_path: Path) -> None:
    source = tmp_path / "sample.py"
    source.write_text(
        '''
def documented() -> str:
    """Return a documented value."""
    return "ok"

def missing() -> str:
    return "missing"
'''.strip(),
        encoding="utf-8",
    )
    docs = collect_functions(source, include_private=False, language="en")
    changed_ranges = {"sample.py": [(1, 7)]}

    analysis = calculate_diff_analysis(
        docs,
        changed_ranges,
        repo_root=tmp_path,
        base_ref="origin/main",
        head_ref="HEAD",
    )

    assert analysis.changed_functions == 2
    assert analysis.documented_functions == 1
    assert analysis.missing_docstrings == 1
    assert analysis.warnings == ["missing()"]
