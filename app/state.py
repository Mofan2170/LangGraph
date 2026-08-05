"""State shared by the LangGraph workflow."""

from typing import Literal, TypedDict

TaskType = Literal[
    "explain_question",
    "analyze_code",
    "diagnose_error",
    "analyze_data",
]

TASK_TYPES: tuple[TaskType, ...] = (
    "explain_question",
    "analyze_code",
    "diagnose_error",
    "analyze_data",
)


class AgentState(TypedDict, total=False):
    user_input: str
    task_type: TaskType
    result: str
    file_name: str
    file_type: str
    file_content: str
