"""
DIY Agent Harness - 主入口

把所有模块组合起来：
- Agent Loop
- Session Manager
- Long-term Memory
- Tool Registry
- RSI System
"""
from __future__ import annotations

from typing import Any, Callable, Optional

from .core.loop import AgentLoop, Tool, AgentResult
from .session.manager import SessionManager, Session
from .memory.long_term import LongTermMemory
from .tools.registry import ToolRegistry, create_builtin_tools
from .rsi.system import RSISystem


class DIYAgentHarness:
    """
    DIY Agent Harness - 完整的 Agent 操作系统

    组合了：
    - Agent Loop：核心推理循环
    - Session Manager：会话管理
    - Long-term Memory：长期记忆
    - Tool Registry：工具系统
    - RSI System：递归自改进
    """

    def __init__(
        self,
        llm_call: Callable[[list[dict], list[dict]], dict[str, Any]],
        system_prompt: str = "You are a helpful assistant.",
        storage_dir: str = ".diy-agent-harness",
        max_steps: int = 20,
        enable_rsi: bool = True,
        enable_memory: bool = True,
    ):
        self.llm_call = llm_call
        self.base_system_prompt = system_prompt
        self.max_steps = max_steps
        self.enable_rsi = enable_rsi
        self.enable_memory = enable_memory

        # 初始化各子系统
        self.session_manager = SessionManager(f"{storage_dir}/sessions")
        self.memory = LongTermMemory(f"{storage_dir}/memory") if enable_memory else None
        self.tools = create_builtin_tools()
        self.rsi = RSISystem(f"{storage_dir}/rsi") if enable_rsi else None

        # 初始化当前会话
        if not self.session_manager.get_current_session():
            self.new_session()

    def new_session(self, title: Optional[str] = None) -> Session:
        """创建新会话"""
        return self.session_manager.create_session(title=title)

    def switch_session(self, session_id: str) -> bool:
        """切换会话"""
        return self.session_manager.switch_session(session_id)

    def list_sessions(self) -> list[dict]:
        """列出所有会话"""
        return self.session_manager.list_sessions()

    def register_tool(self, tool: Tool):
        """注册工具"""
        self.tools.register(tool)

    def add_memory(self, content: str, category: str = "general",
                   importance: float = 0.5) -> None:
        """添加长期记忆"""
        if self.memory:
            self.memory.add(content, category=category, importance=importance)

    def _build_system_prompt(self, task: str) -> str:
        """构建完整的 system prompt"""
        prompt = self.base_system_prompt

        # 注入长期记忆
        if self.memory:
            memory_context = self.memory.get_relevant_for_prompt(task)
            if memory_context:
                prompt += "\n\n" + memory_context

        # 注入 RSI 教训
        if self.rsi:
            rsi_context = self.rsi.build_system_prompt_addition(task)
            if rsi_context:
                prompt += rsi_context

        return prompt

    async def chat(self, user_message: str) -> AgentResult:
        """
        与 Agent 对话

        完整流程：
        1. 构建 system prompt（含记忆 + RSI）
        2. 运行 Agent Loop
        3. 记录经验（RSI）
        4. 返回结果
        """
        # 构建 system prompt
        system_prompt = self._build_system_prompt(user_message)

        # 初始化 Agent Loop
        agent = AgentLoop(
            llm_call=self.llm_call,
            system_prompt=system_prompt,
            max_steps=self.max_steps,
        )

        # 注册所有工具
        for tool_def in self.tools.list_tools():
            agent.register_tool(Tool(
                name=tool_def.name,
                description=tool_def.description,
                parameters=tool_def.parameters,
                handler=tool_def.handler,
            ))

        # 执行
        result = await agent.run(user_message)

        # 记录到会话
        self.session_manager.add_message_to_current("user", user_message)
        self.session_manager.add_message_to_current("assistant", result.final_message)

        # 记录 RSI 经验
        if self.rsi:
            self.rsi.record_experience(
                task=user_message,
                context="",
                action="",
                outcome=result.final_message[:500],
                success=result.success,
                lesson="",  # 可以后续提炼
            )

        return result

    def get_stats(self) -> dict:
        """获取所有子系统的统计信息"""
        stats = {
            "sessions": self.session_manager.list_sessions(),
            "tools": self.tools.get_stats(),
        }

        if self.memory:
            stats["memory"] = self.memory.get_stats()

        if self.rsi:
            stats["rsi"] = self.rsi.get_stats()

        return stats
