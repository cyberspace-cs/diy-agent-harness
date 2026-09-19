"""
Tool System - 工具系统

工具的注册、发现、执行。
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Callable, Optional


@dataclass
class ToolDefinition:
    """工具定义"""
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[[dict[str, Any]], Any]
    category: str = "general"
    enabled: bool = True

    def to_openai_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            }
        }


class ToolRegistry:
    """
    工具注册表

    功能：
    - 注册工具
    - 列出所有工具
    - 按类别过滤
    - 执行工具
    """

    def __init__(self):
        self.tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition):
        """注册一个工具"""
        self.tools[tool.name] = tool

    def unregister(self, name: str) -> bool:
        """注销一个工具"""
        if name in self.tools:
            del self.tools[name]
            return True
        return False

    def get(self, name: str) -> Optional[ToolDefinition]:
        """获取一个工具"""
        return self.tools.get(name)

    def list_tools(self, category: Optional[str] = None,
                   only_enabled: bool = True) -> list[ToolDefinition]:
        """列出工具"""
        tools = list(self.tools.values())
        if only_enabled:
            tools = [t for t in tools if t.enabled]
        if category:
            tools = [t for t in tools if t.category == category]
        return tools

    def get_schemas(self, category: Optional[str] = None) -> list[dict[str, Any]]:
        """获取所有工具的 schema"""
        return [t.to_openai_schema() for t in self.list_tools(category=category)]

    def execute(self, name: str, args: dict[str, Any]) -> Any:
        """执行工具"""
        tool = self.tools.get(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found")
        if not tool.enabled:
            raise ValueError(f"Tool '{name}' is disabled")
        return tool.handler(args)

    def get_stats(self) -> dict:
        """获取工具统计"""
        categories: dict[str, int] = {}
        for t in self.tools.values():
            categories[t.category] = categories.get(t.category, 0) + 1

        return {
            "total": len(self.tools),
            "enabled": sum(1 for t in self.tools.values() if t.enabled),
            "by_category": categories,
        }


# 内置工具示例
def create_builtin_tools() -> ToolRegistry:
    """创建内置工具集"""
    registry = ToolRegistry()

    # 计算器工具
    registry.register(ToolDefinition(
        name="calculator",
        description="Evaluate a mathematical expression",
        parameters={
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "The mathematical expression to evaluate",
                }
            },
            "required": ["expression"],
        },
        handler=lambda args: eval(args["expression"], {"__builtins__": {}}),
        category="utility",
    ))

    # 时间工具
    registry.register(ToolDefinition(
        name="get_current_time",
        description="Get the current date and time",
        parameters={
            "type": "object",
            "properties": {},
        },
        handler=lambda args: str(__import__("datetime").datetime.now()),
        category="utility",
    ))

    return registry
