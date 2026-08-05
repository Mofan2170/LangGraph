"""Data-analysis graph node."""

from app.llm import ask_llm
from app.state import AgentState


def analyze_data_node(state: AgentState) -> AgentState:
    data_text = state.get("file_content") or state.get("user_input", "")
    prompt = f"""
请根据下面内容给出数据分析建议：
1. 说明数据大概属于什么类型
2. 可以做哪些分析
3. 需要重点关注哪些字段
4. 推荐哪些可视化方式
5. 是否适合继续做机器学习建模
6. 指出可能的数据质量风险

数据内容或描述：
{data_text}
"""
    state["result"] = ask_llm(prompt)
    return state
