"""Build the conditional LangGraph workflow."""

from langgraph.graph import END, StateGraph

from app.nodes.analyze_code import analyze_code_node
from app.nodes.analyze_data import analyze_data_node
from app.nodes.classifier import classify_task
from app.nodes.diagnose_error import diagnose_error_node
from app.nodes.explain_question import explain_question_node
from app.state import AgentState, TASK_TYPES

TASK_ROUTES = {task_type: task_type for task_type in TASK_TYPES}


def route_entry(state: AgentState) -> str:
    task_type = state.get("task_type")
    return task_type if task_type in TASK_TYPES else "classifier"


def route_by_task(state: AgentState) -> str:
    return state.get("task_type", "explain_question")


def build_graph():
    builder = StateGraph(AgentState)

    builder.add_node("classifier", classify_task)
    builder.add_node("explain_question", explain_question_node)
    builder.add_node("analyze_code", analyze_code_node)
    builder.add_node("diagnose_error", diagnose_error_node)
    builder.add_node("analyze_data", analyze_data_node)

    builder.set_conditional_entry_point(
        route_entry,
        {"classifier": "classifier", **TASK_ROUTES},
    )
    builder.add_conditional_edges("classifier", route_by_task, TASK_ROUTES)

    for task_type in TASK_TYPES:
        builder.add_edge(task_type, END)

    return builder.compile()


graph = build_graph()
