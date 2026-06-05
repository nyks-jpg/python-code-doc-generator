"""Provider interfaces for future documentation generation backends.

The current CLI remains fully static and offline. This module defines the
small contract future LLM-backed providers can implement without changing the
AST parser or output renderers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence


@dataclass(frozen=True)
class DocumentationRequest:
    """Input passed to a documentation provider."""

    qualified_name: str
    signature: str
    docstring: str | None
    static_summary: str
    static_details: Sequence[str]
    source_excerpt: str | None = None


@dataclass(frozen=True)
class DocumentationResponse:
    """Provider-generated documentation text."""

    summary: str
    details: list[str]
    provider: str


class DocumentationProvider(Protocol):
    """Interface implemented by static or AI-backed documentation providers."""

    name: str

    def generate(self, request: DocumentationRequest) -> DocumentationResponse:
        """Generate documentation text for one function."""


class StaticAnalysisProvider:
    """Provider that preserves the current deterministic static output."""

    name = "static-analysis"

    def generate(self, request: DocumentationRequest) -> DocumentationResponse:
        """Return the static summary and details unchanged."""

        return DocumentationResponse(
            summary=request.static_summary,
            details=list(request.static_details),
            provider=self.name,
        )


def get_documentation_provider(name: str = "static-analysis") -> DocumentationProvider:
    """Return a documentation provider by name."""

    normalized = name.strip().lower()
    if normalized == "static-analysis":
        return StaticAnalysisProvider()
    raise ValueError(f"Unknown documentation provider: {name}")
