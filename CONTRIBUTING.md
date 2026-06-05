# Contributing to python-code-doc-generator

Thank you for your interest in contributing to **python-code-doc-generator**. This project is built as a community-oriented open source tool, not a personal script, and contributions are welcome from developers, maintainers, documentation writers, and platform teams.

## Contribution Rules

If you want to contribute, please follow these basic rules:

1. Fork the repository.
2. Create your own branch for the change.
3. Make sure the GitHub Actions tests pass.
4. Send a Pull Request.

These steps help keep the project reviewable, stable, and easy for new contributors to understand.

## Recommended Workflow

Fork the repository on GitHub, then clone your fork:

```bash
git clone https://github.com/your-username/python-code-doc-generator.git
cd python-code-doc-generator
```

Create a dedicated branch:

```bash
git checkout -b feature/short-description
```

For bug fixes:

```bash
git checkout -b fix/short-description
```

Install dependencies:

```bash
python -m pip install -e ".[dev]"
```

Run the local checks before opening a Pull Request:

```bash
python -m py_compile main.py
python -m pytest
python-code-doc-generator --version
python-code-doc-generator main.py --language en --strict --fail-on-empty --output generated-docs.md
python-code-doc-generator main.py --format json --language en --strict --fail-on-empty --output generated-docs.json
```

If you only want to verify package installation without development tools, run:

```bash
python -m pip install -e .
python-code-doc-generator --version
```

## Pull Request Guidelines

When opening a Pull Request, please include:

- a short summary of what changed,
- why the change is useful,
- any related issue number,
- the commands you ran to validate the change,
- screenshots or output examples if the change affects generated documentation.

Keep Pull Requests focused. A small, well-explained PR is easier to review and merge than a large one that changes unrelated parts of the project.

## Code Guidelines

- Prefer clear, readable Python over clever abstractions.
- Keep the tool lightweight and CLI-friendly.
- Avoid adding dependencies unless they provide clear value.
- Preserve deterministic output for CI/CD usage.
- Update README examples when behavior changes.
- Keep error messages actionable for users.
- Keep package metadata in `pyproject.toml` accurate when changing the public CLI.

## Test Coverage Expectations

Changes to parser behavior should update tests under `tests/test_parser.py`.

Changes to Markdown or JSON output should update tests under `tests/test_renderers.py`.

Changes to CLI flags, exit codes, or output-file behavior should update tests under `tests/test_cli.py`.

The GitHub Actions workflow runs on Python 3.10, 3.11, and 3.12. A Pull Request should be considered ready for review only after these checks pass.

## Good First Contributions

Useful contribution areas include:

- parser accuracy improvements,
- better Markdown output,
- JSON schema improvements,
- test coverage,
- CI/CD examples,
- documentation examples,
- packaging improvements,
- OpenAI integration experiments.

## License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.
