"""Question-explanation graph node."""

from app.llm import ask_llm
from app.state import AgentState


def explain_question_node(state: AgentState) -> AgentState:
    user_input = state.get("file_content") or state.get("user_input", "")
    prompt = f"""
请把下面的题目或任务要求解释清楚，适合大学生理解：
1. 说明题目在问什么
2. 提取核心知识点
3. 给出解题或完成任务的步骤建议

待分析内容：
{user_input}
"""
    state["result"] = ask_llm(prompt)
    return state
