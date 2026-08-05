"""Code-analysis graph node."""

from app.llm import ask_llm
from app.state import AgentState


def analyze_code_node(state: AgentState) -> AgentState:
    code_text = state.get("file_content") or state.get("user_input", "")
    prompt = f"""
请分析下面的代码内容：
1. 说明代码整体作用
2. 按步骤解释核心逻辑
3. 说明输入和输出
4. 指出可能的问题或改进点

代码内容：
{code_text}
"""
    state["result"] = ask_llm(prompt)
    return state
