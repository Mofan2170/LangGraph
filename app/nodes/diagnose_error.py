"""Error-diagnosis graph node."""

from app.llm import ask_llm
from app.state import AgentState


def diagnose_error_node(state: AgentState) -> AgentState:
    user_input = state.get("file_content") or state.get("user_input", "")
    prompt = f"""
请分析下面的报错或异常信息：
1. 解释报错含义
2. 说明常见原因
3. 给出修改建议
4. 尽量给出修复示例

报错内容：
{user_input}
"""
    state["result"] = ask_llm(prompt)
    return state
