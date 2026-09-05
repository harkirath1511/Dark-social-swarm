import pytest
from app.core.config import settings

@pytest.fixture(autouse=True)
def disable_external_llm_during_tests(monkeypatch):
    """Ensures unit tests run offline and deterministically without consuming API rate limits."""
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "")
    monkeypatch.setenv("GROQ_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
