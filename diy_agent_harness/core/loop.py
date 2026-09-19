"""
Agent Loop - 最核心的推理循环

这是 Harness 的心脏：while True + tool calling。
其他所有系统（记忆、工具、上下文）都是围绕这个循环构建的。
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class Tool:
    """一个可调用的工具"""
    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema
    handler: Callable[[dict[str, Any]], str]

    def to_openai_schema(self) -> dict[str, Any]:
        """转换为 OpenAI function calling 格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            }
        }


@dataclass
class Message:
    """一条对话消息"""
    role: str  # system / user / assistant / tool
    content: str
    tool_calls: Optional[list[dict]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None  # tool name

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"role": self.role, "content": self.content}
        if self.tool_calls:
            d["tool_calls"] = self.tool_calls
        if self.tool_call_id:
            d["tool_call_id"] = self.tool_call_id
        if self.name:
            d["name"] = self.name
        return d


@dataclass
class AgentResult:
    """Agent 执行结果"""
    success: bool
    final_message: str
    steps: list[dict[str, Any]] = field(default_factory=list)
    total_tokens: int = 0
    error: Optional[str] = None


class AgentLoop:
    """
    Agent 推理循环

    核心流程：
    1. 把 system prompt + 历史消息 + 工具定义发给 LLM
    2. LLM 返回要么是最终回答，要么是工具调用
    3. 如果是工具调用，执行工具，把结果加回消息历史
    4. 重复直到 LLM 给出最终回答，或达到最大步数
    """

    def __init__(
        self,
        llm_call: Callable[[list[dict], list[dict]], dict[str, Any]],
        system_prompt: str = "You are a helpful assistant.",
        max_steps: int = 20,
    ):
        self.llm_call = llm_call  # 注入的 LLM 调用函数
        self.system_prompt = system_prompt
        self.max_steps = max_steps
        self.tools: dict[str, Tool] = {}
        self.messages: list[Message] = []

    def register_tool(self, tool: Tool):
        """注册一个工具"""
        self.tools[tool.name] = tool

    def _get_tool_schemas(self) -> list[dict[str, Any]]:
        """获取所有工具的 schema"""
        return [t.to_openai_schema() for t in self.tools.values()]

    def _execute_tool_call(self, tool_call: dict[str, Any]) -> str:
        """执行一个工具调用"""
        func_name = tool_call["function"]["name"]
        func_args = json.loads(tool_call["function"]["arguments"])

        if func_name not in self.tools:
            return f"Error: Tool '{func_name}' not found."

        try:
            result = self.tools[func_name].handler(func_args)
            return str(result)
        except Exception as e:
            return f"Error executing tool: {e}"

    async def run(self, user_message: str) -> AgentResult:
        """
        运行 Agent 循环

        Args:
            user_message: 用户输入

        Returns:
            AgentResult: 执行结果
        """
        # 初始化消息历史
        self.messages = [
            Message(role="system", content=self.system_prompt),
            Message(role="user", content=user_message),
        ]

        steps: list[dict[str, Any]] = []

        for step in range(self.max_steps):
            # 转换为 LLM 格式
            messages_dict = [m.to_dict() for m in self.messages]
            tools_schema = self._get_tool_schemas()

            # 调用 LLM
            response = self.llm_call(messages_dict, tools_schema)

            # 解析响应
            assistant_msg = response["choices"][0]["message"]
            tool_calls = assistant_msg.get("tool_calls")

            step_info = {
                "step": step + 1,
                "has_tool_calls": tool_calls is not None,
            }
            steps.append(step_info)

            if not tool_calls:
                # 没有工具调用，这是最终回答
                final_content = assistant_msg.get("content", "")
                return AgentResult(
                    success=True,
                    final_message=final_content,
                    steps=steps,
                    total_tokens=response.get("usage", {}).get("total_tokens", 0),
                )

            # 有工具调用，执行每个工具
            self.messages.append(Message(
                role="assistant",
                content=assistant_msg.get("content", ""),
                tool_calls=tool_calls,
            ))

            for tool_call in tool_calls:
                result = self._execute_tool_call(tool_call)
                self.messages.append(Message(
                    role="tool",
                    content=result,
                    tool_call_id=tool_call["id"],
                    name=tool_call["function"]["name"],
                ))

        # 达到最大步数
        return AgentResult(
            success=False,
            final_message="",
            steps=steps,
            error=f"Reached max steps ({self.max_steps}) without finishing.",
        )

    def get_conversation_history(self) -> list[dict[str, Any]]:
        """获取完整对话历史"""
        return [m.to_dict() for m in self.messages]
