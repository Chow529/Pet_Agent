from typing import Callable
from langchain.agents.middleware import wrap_tool_call,before_model
from langchain.tools.tool_node import ToolCallRequest
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from langgraph.runtime import Runtime
from langchain.agents import AgentState
from utils.logging_tool import logger

@wrap_tool_call
def monitor_tool(
    request:ToolCallRequest,
    handler:Callable[[ToolCallRequest],ToolMessage|Command],
):
    """
    工具执行的监控
    """
    logger.info(f"执行工具 {request.tool_call['name']}")
    logger.info(f"执行工具 {request.tool_call['args']}")

    try:
        res = handler(request)
        logger.info(f"执行工具 {request.tool_call['args']}")
        return res
    except Exception as e:
        logger.error(f"失败 {e}")
        raise e

@before_model
def log_befort_mode(
    state:AgentState,
    runtime:Runtime
):
    """
    log_befort_mode 的 Docstring
    """
    logger.info(f"准备调用模型{state},带有{len(state['messages'])}条消息询问模型")
    return None


# def report_prompt_switch():
#     """
#     动态切换提示词
#     """
#     pass