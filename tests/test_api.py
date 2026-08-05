from fastapi.testclient import TestClient
import pytest

from app import main as main_module
from app.state import AgentState


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    def fake_invoke(state: AgentState) -> AgentState:
        state["task_type"] = state.get("task_type", "explain_question")
        state["result"] = "DEMO_OK"
        return state

    monkeypatch.setattr(main_module, "_invoke_graph", fake_invoke)
    return TestClient(main_module.app)


def test_root_endpoint(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == "DataMentor AI API is running"


def test_analyze_endpoint(client: TestClient) -> None:
    response = client.post("/analyze", json={"user_input": "解释递归"})

    assert response.status_code == 200
    assert response.json() == {
        "task_type": "explain_question",
        "result": "DEMO_OK",
    }


def test_analyze_rejects_blank_input(client: TestClient) -> None:
    response = client.post("/analyze", json={"user_input": "   "})

    assert response.status_code == 422


def test_upload_routes_csv_to_data_analysis(client: TestClient) -> None:
    response = client.post(
        "/upload",
        files={"file": ("sample.csv", b"name,score\nAlice,90\n", "text/csv")},
    )

    assert response.status_code == 200
    assert response.json()["task_type"] == "analyze_data"
    assert response.json()["result"] == "DEMO_OK"


def test_upload_rejects_unsupported_file(client: TestClient) -> None:
    response = client.post(
        "/upload",
        files={"file": ("sample.exe", b"binary", "application/octet-stream")},
    )

    assert response.status_code == 400


def test_upload_rejects_empty_file(client: TestClient) -> None:
    response = client.post(
        "/upload",
        files={"file": ("empty.txt", b"", "text/plain")},
    )

    assert response.status_code == 400


def test_upload_enforces_size_limit(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(main_module, "MAX_UPLOAD_BYTES", 4)

    response = client.post(
        "/upload",
        files={"file": ("large.txt", b"12345", "text/plain")},
    )

    assert response.status_code == 413
