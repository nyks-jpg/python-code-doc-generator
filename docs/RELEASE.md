# Release Guide

This project uses explicit semantic versioning.

## Versioning Strategy

- Patch releases fix bugs without changing CLI behavior.
- Minor releases add backward-compatible CLI flags, output fields, or automation features.
- Major releases may change output schemas, default CI behavior, or supported Python versions.

Keep these values in sync before each release:

- `APP_VERSION` in `main.py`
- `version` in `pyproject.toml`
- Git tag, for example `v0.2.0`

The test suite validates that `main.py` and `pyproject.toml` use the same version.

## Pre-Release Checklist

```bash
python -m pip install -e ".[dev]"
python -m py_compile main.py doc_providers.py
python -m pytest
python -m build
python -m twine check dist/*
```

## Publish To PyPI

Use a PyPI API token configured in your environment.

```bash
python -m twine upload dist/*
```

After publishing, users can install the package with:

```bash
python -m pip install python-code-doc-generator
python-code-doc-generator --version
```

## GitHub Release

1. Create a tag that matches the package version.
2. Push the tag to GitHub.
3. Attach the generated `dist/` artifacts to the GitHub Release if desired.
4. Include a short changelog covering CLI flags, output schema changes, and CI behavior.
