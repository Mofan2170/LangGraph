"""Classify free-form requests into one of the supported task types."""

from app.llm import ask_llm
from app.state import AgentState, TASK_TYPES


def classify_task(state: AgentState) -> AgentState:
    if state.get("task_type") in TASK_TYPES:
        return state

    user_input = state.get("user_input", "")
    prompt = f"""
请判断下面用户请求属于哪一类，只返回以下四个标签之一：
- explain_question
- analyze_code
- diagnose_error
- analyze_data

用户输入：
{user_input}
"""

    raw_result = ask_llm(prompt).strip().lower()
    exact_result = raw_result.strip("` \\t\\r\\n")

    if exact_result in TASK_TYPES:
        task_type = exact_result
    else:
        matches = [label for label in TASK_TYPES if label in raw_result]
        task_type = matches[0] if len(matches) == 1 else "explain_question"

    state["task_type"] = task_type
    return state
