from pathlib import Path
import subprocess

from main import (
    calculate_diff_analysis,
    collect_functions,
    parse_changed_line_ranges,
    run,
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

def missing_docstring() -> str:
    return "missing"

def missing_return():
    """Return a value without an annotation."""
    return "missing annotation"
'''.strip(),
        encoding="utf-8",
    )
    docs = collect_functions(source, include_private=False, language="en")
    changed_ranges = {"sample.py": [(1, 11)]}

    analysis = calculate_diff_analysis(
        docs,
        changed_ranges,
        repo_root=tmp_path,
        base_ref="origin/main",
        head_ref="HEAD",
    )

    assert analysis.changed_functions == 3
    assert analysis.documented_functions == 2
    assert analysis.missing_docstrings == 1
    assert analysis.missing_return_annotations == 1
    assert analysis.missing_docstring_functions == ["missing_docstring()"]
    assert analysis.missing_return_annotation_functions == ["missing_return()"]
    assert analysis.warnings == [
        "Missing docstring: missing_docstring()",
        "Missing return annotation: missing_return()",
    ]


def test_cli_diff_analysis_fails_on_documentation_issues(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=tmp_path,
        check=True,
    )
    source = tmp_path / "sample.py"
    source.write_text(
        '''
def documented() -> str:
    """Return a documented value."""
    return "ok"
'''.strip(),
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "sample.py"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "base"], cwd=tmp_path, check=True)

    source.write_text(
        '''
def documented() -> str:
    """Return a documented value."""
    return "ok"

def added_without_docs():
    return "missing"
'''.strip(),
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "sample.py"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "add undocumented"], cwd=tmp_path, check=True)

    exit_code = run([str(tmp_path), "--diff-base", "HEAD~1", "--language", "en"])

    assert exit_code == 4
