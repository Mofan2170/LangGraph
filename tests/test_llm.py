from types import SimpleNamespace

import pytest

from app import llm


def test_client_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("API_KEY", raising=False)
    llm.get_client.cache_clear()

    with pytest.raises(RuntimeError, match="API_KEY"):
        llm.get_client()


def test_ask_llm_returns_model_content(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class FakeCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            message = SimpleNamespace(content="MODEL_OK")
            return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    fake_client = SimpleNamespace(
        chat=SimpleNamespace(completions=FakeCompletions()),
    )
    monkeypatch.setattr(llm, "get_client", lambda: fake_client)
    monkeypatch.setenv("MODEL_NAME", "demo-model")

    assert llm.ask_llm("hello") == "MODEL_OK"
    assert captured["model"] == "demo-model"


def test_ask_llm_rejects_an_empty_prompt() -> None:
    with pytest.raises(ValueError, match="不能为空"):
        llm.ask_llm("   ")
