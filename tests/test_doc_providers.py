import pytest

from doc_providers import DocumentationRequest, get_documentation_provider


def test_static_provider_preserves_static_documentation() -> None:
    provider = get_documentation_provider()
    request = DocumentationRequest(
        qualified_name="sample.add",
        signature="def add(left: int, right: int) -> int",
        docstring="Add two numbers.",
        static_summary="Adds two numbers.",
        static_details=["Accepts `left`, `right` as input."],
    )

    response = provider.generate(request)

    assert response.provider == "static-analysis"
    assert response.summary == "Adds two numbers."
    assert response.details == ["Accepts `left`, `right` as input."]


def test_unknown_provider_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unknown documentation provider"):
        get_documentation_provider("openai")
