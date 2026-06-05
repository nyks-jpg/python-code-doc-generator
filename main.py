"""Python Code Doc-Generator.

A lightweight command-line tool that scans Python source files, extracts
function definitions, and generates readable documentation from static code
analysis.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence


APP_NAME = "Python Code Doc-Generator"
APP_VERSION = "0.2.0"


class AppError(Exception):
    """Raised when the CLI receives invalid input or cannot finish safely."""


@dataclass
class ParameterDoc:
    """Structured information about a function parameter."""

    name: str
    kind: str
    annotation: str | None = None
    default: str | None = None


@dataclass
class FunctionDoc:
    """Structured documentation for one discovered function."""

    file: str
    name: str
    qualified_name: str
    kind: str
    line: int
    end_line: int | None
    signature: str
    parameters: list[ParameterDoc]
    returns: str | None
    decorators: list[str]
    raises: list[str]
    docstring: str | None
    summary: str
    details: list[str]


@dataclass
class CoverageSummary:
    """Documentation coverage metrics for a scan."""

    percentage: int
    total_functions: int
    documented_functions: int
    undocumented_functions: int


@dataclass
class DiffAnalysis:
    """Documentation status for functions touched by a git diff."""

    base_ref: str
    head_ref: str
    changed_functions: int
    documented_functions: int
    missing_docstrings: int
    warnings: list[str]


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        prog="python-code-doc-generator",
        description=(
            "Scan Python files and generate function-level documentation "
            "from static code analysis."
        ),
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Python file or directory to scan.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Optional output file. If omitted, documentation is printed.",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format. Default: markdown.",
    )
    parser.add_argument(
        "--language",
        choices=("tr", "en"),
        default="tr",
        help="Documentation language for generated explanations. Default: tr.",
    )
    parser.add_argument(
        "--include-private",
        action="store_true",
        help="Include functions whose names start with an underscore.",
    )
    parser.add_argument(
        "--no-recursive",
        dest="recursive",
        action="store_false",
        help="When PATH is a directory, scan only its top-level Python files.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return a non-zero exit code if any file cannot be parsed.",
    )
    parser.add_argument(
        "--fail-on-empty",
        action="store_true",
        help="Return a non-zero exit code when no functions are discovered.",
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Include function docstring coverage metrics in the output.",
    )
    parser.add_argument(
        "--diff-base",
        help=(
            "Git base ref for diff-aware documentation analysis, "
            "for example origin/main."
        ),
    )
    parser.add_argument(
        "--diff-head",
        default="HEAD",
        help="Git head ref for diff-aware analysis. Default: HEAD.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"{APP_NAME} {APP_VERSION}",
    )
    return parser.parse_args(argv)


def discover_python_files(path: Path, recursive: bool) -> list[Path]:
    """Return the Python files represented by the requested path."""

    resolved = path.expanduser().resolve()
    if not resolved.exists():
        raise AppError(f"Path does not exist: {resolved}")

    if resolved.is_file():
        if resolved.suffix != ".py":
            raise AppError(f"Expected a .py file, received: {resolved}")
        return [resolved]

    if not resolved.is_dir():
        raise AppError(f"Path is not a file or directory: {resolved}")

    pattern = "**/*.py" if recursive else "*.py"
    files = sorted(file for file in resolved.glob(pattern) if file.is_file())
    if not files:
        raise AppError(f"No Python files found under: {resolved}")
    return files


def read_source(path: Path) -> str:
    """Read Python source with a predictable encoding strategy."""

    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise AppError(f"Could not read {path}: {exc}") from exc


def parse_python_source(path: Path, source: str) -> ast.Module:
    """Parse a Python file and convert syntax errors into clear CLI errors."""

    try:
        return ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        line = exc.lineno or "unknown"
        message = exc.msg or "invalid syntax"
        raise AppError(f"Syntax error in {path}:{line}: {message}") from exc


class FunctionCollector(ast.NodeVisitor):
    """Collect function metadata while preserving class and nested scopes."""

    def __init__(self, file_path: Path, include_private: bool, language: str) -> None:
        self.file_path = file_path
        self.include_private = include_private
        self.language = language
        self.scope_stack: list[tuple[str, str]] = []
        self.functions: list[FunctionDoc] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: N802
        self.scope_stack.append(("class", node.name))
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        self._visit_function(node, is_async=False)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        self._visit_function(node, is_async=True)

    def _visit_function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        *,
        is_async: bool,
    ) -> None:
        if self.include_private or not node.name.startswith("_"):
            self.functions.append(self._build_doc(node, is_async=is_async))

        self.scope_stack.append(("function", node.name))
        self.generic_visit(node)
        self.scope_stack.pop()

    def _build_doc(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        *,
        is_async: bool,
    ) -> FunctionDoc:
        qualified_name = ".".join([name for _, name in self.scope_stack] + [node.name])
        parameters = extract_parameters(node.args)
        returns = safe_unparse(node.returns)
        decorators = [safe_unparse(decorator) for decorator in node.decorator_list]
        raises = sorted(extract_raised_exceptions(node))
        docstring = clean_docstring(ast.get_docstring(node))
        kind = function_kind(self.scope_stack, is_async=is_async)
        signature = build_signature(node.name, parameters, returns, is_async=is_async)
        summary = generate_summary(
            qualified_name=qualified_name,
            node_name=node.name,
            kind=kind,
            docstring=docstring,
            language=self.language,
        )
        details = generate_details(
            parameters=parameters,
            returns=returns,
            raises=raises,
            decorators=decorators,
            is_async=is_async,
            language=self.language,
        )

        return FunctionDoc(
            file=str(self.file_path),
            name=node.name,
            qualified_name=qualified_name,
            kind=kind,
            line=node.lineno,
            end_line=getattr(node, "end_lineno", None),
            signature=signature,
            parameters=parameters,
            returns=returns,
            decorators=decorators,
            raises=raises,
            docstring=docstring,
            summary=summary,
            details=details,
        )


def collect_functions(path: Path, include_private: bool, language: str) -> list[FunctionDoc]:
    """Parse one file and return all discovered functions."""

    source = read_source(path)
    tree = parse_python_source(path, source)
    collector = FunctionCollector(path, include_private=include_private, language=language)
    collector.visit(tree)
    return collector.functions


def calculate_coverage(functions: Sequence[FunctionDoc]) -> CoverageSummary:
    """Calculate function-level docstring coverage."""

    total = len(functions)
    documented = sum(1 for item in functions if item.docstring)
    undocumented = total - documented
    percentage = round((documented / total) * 100) if total else 0
    return CoverageSummary(
        percentage=percentage,
        total_functions=total,
        documented_functions=documented,
        undocumented_functions=undocumented,
    )


def coverage_lines(summary: CoverageSummary) -> list[str]:
    """Render coverage metrics as text lines."""

    return [
        f"Documentation Coverage: {summary.percentage}%",
        f"Total Functions: {summary.total_functions}",
        f"Documented Functions: {summary.documented_functions}",
        f"Undocumented Functions: {summary.undocumented_functions}",
    ]


def resolve_git_root(path: Path) -> Path:
    """Return the git repository root for a path."""

    start_path = path if path.is_dir() else path.parent
    try:
        result = subprocess.run(
            ["git", "-C", str(start_path), "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise AppError(
            "Could not locate a git repository for diff-aware analysis."
        ) from exc
    return Path(result.stdout.strip()).resolve()


def get_changed_line_ranges(
    repo_root: Path,
    base_ref: str,
    head_ref: str,
) -> dict[str, list[tuple[int, int]]]:
    """Return changed new-file line ranges from a git diff."""

    range_spec = f"{base_ref}...{head_ref}"
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(repo_root),
                "diff",
                "--no-ext-diff",
                "--unified=0",
                "--diff-filter=AMR",
                range_spec,
                "--",
                "*.py",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise AppError(
            f"Could not compute git diff for {range_spec}. "
            "Make sure the refs exist in the local checkout."
        ) from exc
    return parse_changed_line_ranges(result.stdout)


def parse_changed_line_ranges(diff_text: str) -> dict[str, list[tuple[int, int]]]:
    """Parse git unified diff hunks into changed new-file line ranges."""

    ranges: dict[str, list[tuple[int, int]]] = {}
    current_file: str | None = None
    for line in diff_text.splitlines():
        if line.startswith("+++ "):
            current_file = parse_diff_new_file(line)
            if current_file:
                ranges.setdefault(current_file, [])
            continue

        if current_file and line.startswith("@@ "):
            match = re.search(r"\+(\d+)(?:,(\d+))?", line)
            if not match:
                continue
            start = int(match.group(1))
            count = int(match.group(2) or "1")
            if count == 0:
                continue
            ranges[current_file].append((start, start + count - 1))
    return {path: items for path, items in ranges.items() if items}


def parse_diff_new_file(line: str) -> str | None:
    """Return a normalized new-file path from a git diff +++ line."""

    marker = line[4:].strip()
    if marker == "/dev/null":
        return None
    if marker.startswith("b/"):
        marker = marker[2:]
    return marker.replace("\\", "/")


def calculate_diff_analysis(
    functions: Sequence[FunctionDoc],
    changed_ranges: dict[str, list[tuple[int, int]]],
    repo_root: Path,
    base_ref: str,
    head_ref: str,
) -> DiffAnalysis:
    """Analyze documentation status for changed functions."""

    changed_functions = [
        item
        for item in functions
        if function_overlaps_changed_ranges(item, changed_ranges, repo_root)
    ]
    documented = sum(1 for item in changed_functions if item.docstring)
    warnings = [
        f"{item.qualified_name}()"
        for item in changed_functions
        if not item.docstring
    ]
    return DiffAnalysis(
        base_ref=base_ref,
        head_ref=head_ref,
        changed_functions=len(changed_functions),
        documented_functions=documented,
        missing_docstrings=len(warnings),
        warnings=warnings,
    )


def function_overlaps_changed_ranges(
    function: FunctionDoc,
    changed_ranges: dict[str, list[tuple[int, int]]],
    repo_root: Path,
) -> bool:
    """Return whether a function overlaps changed diff lines."""

    relative_path = relative_to_repo(Path(function.file), repo_root)
    ranges = changed_ranges.get(relative_path, [])
    function_end = function.end_line or function.line
    return any(start <= function_end and end >= function.line for start, end in ranges)


def relative_to_repo(path: Path, repo_root: Path) -> str:
    """Return a POSIX path relative to the git repository root."""

    try:
        return path.resolve().relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def diff_analysis_lines(analysis: DiffAnalysis) -> list[str]:
    """Render diff-aware analysis as text lines."""

    lines = [
        f"Changed Functions: {analysis.changed_functions}",
        f"Documented: {analysis.documented_functions}",
        f"Missing Docstrings: {analysis.missing_docstrings}",
        "",
        "Warnings:",
    ]
    if analysis.warnings:
        lines.extend(f"* {name}" for name in analysis.warnings)
    else:
        lines.append("None")
    return lines


def extract_parameters(args: ast.arguments) -> list[ParameterDoc]:
    """Extract parameter names, kinds, annotations, and defaults."""

    parameters: list[ParameterDoc] = []
    positional_args = list(args.posonlyargs) + list(args.args)
    defaults = align_defaults(positional_args, args.defaults)

    for arg in args.posonlyargs:
        parameters.append(parameter_from_arg(arg, "positional-only", defaults.get(arg.arg)))

    for arg in args.args:
        parameters.append(parameter_from_arg(arg, "positional-or-keyword", defaults.get(arg.arg)))

    if args.vararg:
        parameters.append(parameter_from_arg(args.vararg, "var-positional", None, prefix="*"))

    for arg, default in zip(args.kwonlyargs, args.kw_defaults):
        parameters.append(parameter_from_arg(arg, "keyword-only", safe_unparse(default)))

    if args.kwarg:
        parameters.append(parameter_from_arg(args.kwarg, "var-keyword", None, prefix="**"))

    return parameters


def align_defaults(args: Sequence[ast.arg], defaults: Sequence[ast.expr]) -> dict[str, str | None]:
    """Map positional arguments to their default values."""

    offset = len(args) - len(defaults)
    result: dict[str, str | None] = {}
    for index, arg in enumerate(args):
        default_index = index - offset
        result[arg.arg] = safe_unparse(defaults[default_index]) if default_index >= 0 else None
    return result


def parameter_from_arg(
    arg: ast.arg,
    kind: str,
    default: str | None,
    *,
    prefix: str = "",
) -> ParameterDoc:
    """Convert an AST argument node into a serializable parameter object."""

    return ParameterDoc(
        name=f"{prefix}{arg.arg}",
        kind=kind,
        annotation=safe_unparse(arg.annotation),
        default=default,
    )


def extract_raised_exceptions(node: ast.AST) -> set[str]:
    """Collect exception names raised directly inside a function body."""

    collector = RaiseCollector()
    body = getattr(node, "body", None)
    if isinstance(body, list):
        for statement in body:
            collector.visit(statement)
    else:
        collector.visit(node)
    return {item for item in collector.raises if item}


class RaiseCollector(ast.NodeVisitor):
    """Collect raise statements without descending into nested scopes."""

    def __init__(self) -> None:
        self.raises: set[str] = set()

    def visit_Raise(self, node: ast.Raise) -> None:  # noqa: N802
        self.raises.add(extract_raise_name(node.exc))

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        return

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        return

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: N802
        return


def extract_raise_name(node: ast.AST | None) -> str:
    """Return a readable exception name for a raise statement."""

    if node is None:
        return "re-raise"
    if isinstance(node, ast.Call):
        return safe_unparse(node.func) or "unknown"
    return safe_unparse(node) or "unknown"


def function_kind(scope_stack: Sequence[tuple[str, str]], *, is_async: bool) -> str:
    """Classify a function based on scope and async syntax."""

    is_method = bool(scope_stack and scope_stack[-1][0] == "class")
    if is_method and is_async:
        return "async method"
    if is_method:
        return "method"
    if is_async:
        return "async function"
    return "function"


def build_signature(
    name: str,
    parameters: Sequence[ParameterDoc],
    returns: str | None,
    *,
    is_async: bool,
) -> str:
    """Build a compact function signature for documentation output."""

    rendered_parameters = ", ".join(render_signature_parameters(parameters))
    async_prefix = "async " if is_async else ""
    return_annotation = f" -> {returns}" if returns else ""
    return f"{async_prefix}def {name}({rendered_parameters}){return_annotation}"


def render_signature_parameters(parameters: Sequence[ParameterDoc]) -> list[str]:
    """Render parameters with Python signature separators."""

    rendered: list[str] = []
    has_var_positional = False
    inserted_keyword_marker = False

    for index, parameter in enumerate(parameters):
        if (
            parameter.kind == "keyword-only"
            and not has_var_positional
            and not inserted_keyword_marker
        ):
            rendered.append("*")
            inserted_keyword_marker = True

        rendered.append(render_parameter(parameter))

        if parameter.kind == "var-positional":
            has_var_positional = True

        next_parameter = parameters[index + 1] if index + 1 < len(parameters) else None
        if parameter.kind == "positional-only" and (
            next_parameter is None or next_parameter.kind != "positional-only"
        ):
            rendered.append("/")

    return rendered


def render_parameter(parameter: ParameterDoc) -> str:
    """Render a parameter for display inside a signature."""

    rendered = parameter.name
    if parameter.annotation:
        rendered = f"{rendered}: {parameter.annotation}"
    if parameter.default is not None:
        rendered = f"{rendered} = {parameter.default}"
    return rendered


def safe_unparse(node: ast.AST | None) -> str | None:
    """Return Python source for an AST node without leaking parser exceptions."""

    if node is None:
        return None
    try:
        return ast.unparse(node)
    except Exception:
        return None


def clean_docstring(docstring: str | None) -> str | None:
    """Normalize docstrings for compact CLI output."""

    if not docstring:
        return None
    return " ".join(docstring.strip().split())


def generate_summary(
    *,
    qualified_name: str,
    node_name: str,
    kind: str,
    docstring: str | None,
    language: str,
) -> str:
    """Create a human-readable summary for a function."""

    if docstring:
        first_sentence = split_first_sentence(docstring)
        if language == "tr":
            return f"`{qualified_name}` mevcut docstring'e göre şunu yapar: {first_sentence}"
        return f"`{qualified_name}` is documented as: {first_sentence}"

    readable_name = humanize_identifier(node_name)
    inferred_action = infer_action(node_name, language)

    if language == "tr":
        type_label = translate_kind(kind)
        return f"`{qualified_name}` {type_label}; {readable_name} işlemini {inferred_action}."

    return f"`{qualified_name}` is a {kind} designed to {inferred_action} {readable_name}."


def generate_details(
    *,
    parameters: Sequence[ParameterDoc],
    returns: str | None,
    raises: Sequence[str],
    decorators: Sequence[str | None],
    is_async: bool,
    language: str,
) -> list[str]:
    """Generate explanatory details from discovered metadata."""

    visible_parameters = [param for param in parameters if param.name not in {"self", "cls"}]
    details: list[str] = []

    if language == "tr":
        if visible_parameters:
            names = ", ".join(f"`{param.name}`" for param in visible_parameters)
            details.append(f"Parametre olarak {names} alır.")
        else:
            details.append("Dışarıdan parametre almadan çalışır.")

        if returns:
            details.append(f"`{returns}` tipinde ya da bu ifadeyle uyumlu bir değer döndürmesi beklenir.")
        else:
            details.append("Belirgin bir dönüş tipi anotasyonu bulunmuyor.")

        if raises:
            details.append(f"Doğrudan fırlatılan hata türleri: {', '.join(f'`{item}`' for item in raises)}.")
        if any(decorators):
            details.append("Dekoratörlerle davranışı genişletilmiştir.")
        if is_async:
            details.append("Asenkron çalıştığı için bir event loop içinde beklenerek kullanılmalıdır.")
        return details

    if visible_parameters:
        names = ", ".join(f"`{param.name}`" for param in visible_parameters)
        details.append(f"Accepts {names} as input.")
    else:
        details.append("Runs without external parameters.")

    if returns:
        details.append(f"Expected to return a value compatible with `{returns}`.")
    else:
        details.append("No explicit return type annotation was found.")

    if raises:
        details.append(f"Directly raises: {', '.join(f'`{item}`' for item in raises)}.")
    if any(decorators):
        details.append("Its behavior is extended with decorators.")
    if is_async:
        details.append("Must be awaited inside an event loop.")
    return details


def split_first_sentence(text: str) -> str:
    """Return the first sentence-like segment from a longer block of text."""

    match = re.search(r"(.+?[.!?])(?:\s|$)", text)
    return match.group(1).strip() if match else text.strip()


def humanize_identifier(identifier: str) -> str:
    """Convert a Python identifier into readable words."""

    identifier = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", identifier)
    return identifier.replace("_", " ").strip().lower() or "operation"


def infer_action(identifier: str, language: str) -> str:
    """Infer a simple action phrase from a function name."""

    lower_name = identifier.lower()
    english_actions = {
        "get": "retrieve",
        "fetch": "fetch",
        "load": "load",
        "read": "read",
        "write": "write",
        "save": "save",
        "create": "create",
        "build": "build",
        "make": "create",
        "parse": "parse",
        "validate": "validate",
        "check": "check",
        "format": "format",
        "render": "render",
        "calculate": "calculate",
        "compute": "compute",
        "convert": "convert",
        "send": "send",
        "handle": "handle",
        "update": "update",
        "delete": "delete",
        "remove": "remove",
    }
    turkish_actions = {
        "get": "almak için kullanılır",
        "fetch": "uzak kaynaktan çekmek için kullanılır",
        "load": "yüklemek için kullanılır",
        "read": "okumak için kullanılır",
        "write": "yazmak için kullanılır",
        "save": "kaydetmek için kullanılır",
        "create": "oluşturmak için kullanılır",
        "build": "inşa etmek için kullanılır",
        "make": "oluşturmak için kullanılır",
        "parse": "ayrıştırmak için kullanılır",
        "validate": "doğrulamak için kullanılır",
        "check": "kontrol etmek için kullanılır",
        "format": "biçimlendirmek için kullanılır",
        "render": "oluşturup sunmak için kullanılır",
        "calculate": "hesaplamak için kullanılır",
        "compute": "hesaplamak için kullanılır",
        "convert": "dönüştürmek için kullanılır",
        "send": "göndermek için kullanılır",
        "handle": "işlemek için kullanılır",
        "update": "güncellemek için kullanılır",
        "delete": "silmek için kullanılır",
        "remove": "kaldırmak için kullanılır",
    }

    action_map = turkish_actions if language == "tr" else english_actions
    for prefix, action in action_map.items():
        if lower_name.startswith(prefix):
            return action
    return "carry out" if language == "en" else "gerçekleştirmek için kullanılır"


def translate_kind(kind: str) -> str:
    """Translate function kind labels for Turkish documentation."""

    translations = {
        "function": "bir fonksiyondur",
        "method": "bir metottur",
        "async function": "asenkron bir fonksiyondur",
        "async method": "asenkron bir metottur",
    }
    return translations.get(kind, kind)


def format_markdown(
    functions: Sequence[FunctionDoc],
    language: str,
    coverage: CoverageSummary | None = None,
    diff_analysis: DiffAnalysis | None = None,
) -> str:
    """Render collected documentation as Markdown."""

    if language == "tr":
        return format_markdown_tr(functions, coverage, diff_analysis)
    return format_markdown_en(functions, coverage, diff_analysis)


def format_markdown_tr(
    functions: Sequence[FunctionDoc],
    coverage: CoverageSummary | None = None,
    diff_analysis: DiffAnalysis | None = None,
) -> str:
    """Render collected documentation as Turkish Markdown."""

    lines = [
        "# Python Kod Dokümantasyonu",
        "",
        f"_Bu doküman {APP_NAME} tarafından statik analiz ile üretilmiştir._",
        "",
    ]
    extend_report_sections(lines, coverage, diff_analysis)

    if not functions:
        lines.extend(["Fonksiyon bulunamadı.", ""])
        return "\n".join(lines)

    for file_path, items in group_by_file(functions):
        lines.extend([f"## `{file_path}`", ""])
        for item in items:
            lines.extend(
                [
                    f"### `{item.qualified_name}`",
                    "",
                    f"- Tür: `{translate_kind(item.kind)}`",
                    f"- Satır: `{format_line_range(item.line, item.end_line)}`",
                    f"- İmza: `{item.signature}`",
                    f"- Özet: {item.summary}",
                ]
            )
            lines.extend(render_markdown_parameters(item.parameters, language="tr"))
            if item.returns:
                lines.append(f"- Dönüş: `{item.returns}`")
            if item.raises:
                lines.append(f"- Hatalar: {', '.join(f'`{name}`' for name in item.raises)}")
            if item.decorators:
                lines.append(f"- Dekoratörler: {', '.join(f'`{name}`' for name in item.decorators if name)}")
            if item.docstring:
                lines.append(f"- Mevcut docstring: {item.docstring}")
            lines.append("- Analiz:")
            for detail in item.details:
                lines.append(f"  - {detail}")
            lines.append("")
    return "\n".join(lines)


def format_markdown_en(
    functions: Sequence[FunctionDoc],
    coverage: CoverageSummary | None = None,
    diff_analysis: DiffAnalysis | None = None,
) -> str:
    """Render collected documentation as English Markdown."""

    lines = [
        "# Python Code Documentation",
        "",
        f"_Generated by {APP_NAME} through static analysis._",
        "",
    ]
    extend_report_sections(lines, coverage, diff_analysis)

    if not functions:
        lines.extend(["No functions were found.", ""])
        return "\n".join(lines)

    for file_path, items in group_by_file(functions):
        lines.extend([f"## `{file_path}`", ""])
        for item in items:
            lines.extend(
                [
                    f"### `{item.qualified_name}`",
                    "",
                    f"- Kind: `{item.kind}`",
                    f"- Lines: `{format_line_range(item.line, item.end_line)}`",
                    f"- Signature: `{item.signature}`",
                    f"- Summary: {item.summary}",
                ]
            )
            lines.extend(render_markdown_parameters(item.parameters, language="en"))
            if item.returns:
                lines.append(f"- Returns: `{item.returns}`")
            if item.raises:
                lines.append(f"- Raises: {', '.join(f'`{name}`' for name in item.raises)}")
            if item.decorators:
                lines.append(f"- Decorators: {', '.join(f'`{name}`' for name in item.decorators if name)}")
            if item.docstring:
                lines.append(f"- Existing docstring: {item.docstring}")
            lines.append("- Analysis:")
            for detail in item.details:
                lines.append(f"  - {detail}")
            lines.append("")
    return "\n".join(lines)


def extend_report_sections(
    lines: list[str],
    coverage: CoverageSummary | None,
    diff_analysis: DiffAnalysis | None,
) -> None:
    """Append optional CI-friendly report summaries to Markdown output."""

    if coverage:
        lines.extend(["## Documentation Coverage", "", "```text"])
        lines.extend(coverage_lines(coverage))
        lines.extend(["```", ""])

    if diff_analysis:
        lines.extend(["## Diff-Aware Pull Request Analysis", "", "```text"])
        lines.extend(diff_analysis_lines(diff_analysis))
        lines.extend(["```", ""])


def render_markdown_parameters(parameters: Sequence[ParameterDoc], language: str) -> list[str]:
    """Render parameter metadata for Markdown output."""

    if not parameters:
        return []

    heading = "- Parametreler:" if language == "tr" else "- Parameters:"
    lines = [heading]
    for parameter in parameters:
        pieces = [f"kind `{parameter.kind}`"]
        if parameter.annotation:
            pieces.append(f"type `{parameter.annotation}`")
        if parameter.default is not None:
            pieces.append(f"default `{parameter.default}`")
        lines.append(f"  - `{parameter.name}` ({', '.join(pieces)})")
    return lines


def group_by_file(functions: Sequence[FunctionDoc]) -> Iterable[tuple[str, list[FunctionDoc]]]:
    """Yield function docs grouped by source file in discovery order."""

    grouped: dict[str, list[FunctionDoc]] = {}
    for item in functions:
        grouped.setdefault(item.file, []).append(item)
    return grouped.items()


def format_line_range(line: int, end_line: int | None) -> str:
    """Format a source line range."""

    if end_line is None or end_line == line:
        return str(line)
    return f"{line}-{end_line}"


def format_json(
    functions: Sequence[FunctionDoc],
    coverage: CoverageSummary | None = None,
    diff_analysis: DiffAnalysis | None = None,
) -> str:
    """Render collected documentation as formatted JSON."""

    function_payload = [asdict(item) for item in functions]
    if coverage is None and diff_analysis is None:
        return json.dumps(function_payload, ensure_ascii=False, indent=2)

    payload: dict[str, object] = {}
    if coverage:
        payload["coverage"] = asdict(coverage)
    if diff_analysis:
        payload["diff_analysis"] = asdict(diff_analysis)
    payload["functions"] = function_payload
    return json.dumps(payload, ensure_ascii=False, indent=2)


def write_output(content: str, output: Path | None) -> None:
    """Write documentation to stdout or an output file."""

    if output is None:
        print(content)
        return

    destination = output.expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")


def print_terminal_report(
    coverage: CoverageSummary | None,
    diff_analysis: DiffAnalysis | None,
) -> None:
    """Print CI-friendly summary lines without corrupting Markdown stdout."""

    lines: list[str] = []
    if coverage:
        lines.extend(coverage_lines(coverage))
    if diff_analysis:
        if lines:
            lines.append("")
        lines.extend(diff_analysis_lines(diff_analysis))
    if lines:
        print("\n".join(lines), file=sys.stderr)


def run(argv: Sequence[str]) -> int:
    """Run the CLI and return a process exit code."""

    args = parse_args(argv)
    files = discover_python_files(args.path, recursive=args.recursive)

    all_functions: list[FunctionDoc] = []
    parse_errors: list[str] = []
    for file_path in files:
        try:
            all_functions.extend(
                collect_functions(
                    file_path,
                    include_private=args.include_private,
                    language=args.language,
                )
            )
        except AppError as exc:
            parse_errors.append(str(exc))

    if parse_errors:
        for error in parse_errors:
            print(f"warning: {error}", file=sys.stderr)
        if args.strict:
            return 2

    if args.fail_on_empty and not all_functions:
        print("No functions were discovered.", file=sys.stderr)
        return 3

    coverage = calculate_coverage(all_functions) if args.coverage else None
    diff_analysis = None
    if args.diff_base:
        repo_root = resolve_git_root(args.path.expanduser().resolve())
        changed_ranges = get_changed_line_ranges(
            repo_root,
            base_ref=args.diff_base,
            head_ref=args.diff_head,
        )
        diff_analysis = calculate_diff_analysis(
            all_functions,
            changed_ranges,
            repo_root,
            base_ref=args.diff_base,
            head_ref=args.diff_head,
        )

    if args.format == "json":
        content = format_json(all_functions, coverage=coverage, diff_analysis=diff_analysis)
    else:
        content = format_markdown(
            all_functions,
            language=args.language,
            coverage=coverage,
            diff_analysis=diff_analysis,
        )

    write_output(content, args.output)
    if args.output is not None or args.format == "json":
        print_terminal_report(coverage, diff_analysis)
    return 0 if not parse_errors else 1


def main() -> None:
    """Program entry point."""

    try:
        raise SystemExit(run(sys.argv[1:]))
    except AppError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
