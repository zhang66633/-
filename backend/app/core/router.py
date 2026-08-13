"""动态路由逻辑 - plan_execution → first_agent, agent → next_agent/format_response."""

from .state import AgentState


def route_to_first_agent(state: AgentState) -> str:
    """根据执行计划，路由到第一个 agent 节点。
    
    如果计划为空或所有步骤完成，直接跳到 format_response。
    """
    plan = state.get("execution_plan", [])
    if not plan:
        return "format_response"

    first_step = plan[0]
    node_map = {
        "analysis": "analysis_agent",
        "modeling": "modeling_agent",
        "data_preprocessing": "data_preprocessing_agent",
        "solving": "solving_agent",
        "verification": "verification_agent",
        "export_results": "export_results_agent",
        "writing": "writing_agent",
    }
    return node_map.get(first_step, "analysis_agent")


def after_agent_router(state: AgentState) -> str:
    """每个 agent 执行完后，路由到下一个 agent 或 format_response。
    
    如果验证未通过且未超过最大重试次数，回退到 rollback_target。
    """
    plan = state.get("execution_plan", [])
    current_idx = state.get("current_step_index", 0)
    max_retries = state.get("max_retries", 3)
    retry_count = state.get("retry_count", 0)

    # 验证回退：如果验证未通过且未超重试限制
    if (not state.get("verification_passed", True) 
            and retry_count <= max_retries
            and state.get("rollback_target")):
        target = state["rollback_target"]
        node_map = {
            "analysis": "analysis_agent",
            "modeling": "modeling_agent",
            "data_preprocessing": "data_preprocessing_agent",
            "solving": "solving_agent",
            "verification": "verification_agent",
            "export_results": "export_results_agent",
            "writing": "writing_agent",
        }
        return node_map.get(target, "modeling_agent")

    # 正常流程：检查下一个步骤
    next_idx = current_idx + 1
    if next_idx >= len(plan):
        return "format_response"

    next_step = plan[next_idx]
    node_map = {
        "analysis": "analysis_agent",
        "modeling": "modeling_agent",
        "data_preprocessing": "data_preprocessing_agent",
        "solving": "solving_agent",
        "verification": "verification_agent",
        "export_results": "export_results_agent",
        "writing": "writing_agent",
    }
    return node_map.get(next_step, "format_response")
