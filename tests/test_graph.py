import pytest

import app.nodes.analyze_code as code_module
import app.nodes.analyze_data as data_module
import app.nodes.classifier as classifier_module
import app.nodes.diagnose_error as error_module
import app.nodes.explain_question as question_module
from app.graph import graph


@pytest.fixture(autouse=True)
def mock_model_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(classifier_module, "ask_llm", lambda _prompt: "diagnose_error")
    monkeypatch.setattr(question_module, "ask_llm", lambda _prompt: "QUESTION_OK")
    monkeypatch.setattr(code_module, "ask_llm", lambda _prompt: "CODE_OK")
    monkeypatch.setattr(error_module, "ask_llm", lambda _prompt: "ERROR_OK")
    monkeypatch.setattr(data_module, "ask_llm", lambda _prompt: "DATA_OK")


def test_classifier_routes_a_free_form_request() -> None:
    result = graph.invoke({"user_input": "这里有一个报错"})

    assert result["task_type"] == "diagnose_error"
    assert result["result"] == "ERROR_OK"


@pytest.mark.parametrize(
    ("task_type", "expected"),
    [
        ("explain_question", "QUESTION_OK"),
        ("analyze_code", "CODE_OK"),
        ("diagnose_error", "ERROR_OK"),
        ("analyze_data", "DATA_OK"),
    ],
)
def test_preselected_task_skips_classification(task_type: str, expected: str) -> None:
    result = graph.invoke(
        {
            "user_input": "demo",
            "task_type": task_type,
            "file_content": "sample content",
        }
    )

    assert result["task_type"] == task_type
    assert result["result"] == expected


def test_classifier_accepts_a_label_inside_markdown(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(classifier_module, "ask_llm", lambda _prompt: "`analyze_code`")

    result = graph.invoke({"user_input": "请看这段代码"})

    assert result["task_type"] == "analyze_code"
    assert result["result"] == "CODE_OK"
