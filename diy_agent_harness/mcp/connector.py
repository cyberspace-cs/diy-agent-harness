"""
MCP Connectors - MCP (Model Context Protocol) 连接器

让 Agent 可以连接到外部 MCP 服务器，使用外部工具。
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class MCPTool:
    """一个从 MCP 服务器获取的工具"""
    name: str
    description: str
    server_name: str  # 来自哪个 MCP 服务器
    parameters: dict[str, Any] = field(default_factory=dict)


class MCPConnector:
    """
    MCP 连接器

    功能：
    - 连接到 MCP 服务器
    - 发现服务器提供的工具
    - 调用远程工具
    """

    def __init__(self):
        self.servers: dict[str, dict] = {}  # server_name -> server_info
        self.tools: dict[str, MCPTool] = {}  # tool_name -> tool_info
        self.tool_handlers: dict[str, Callable] = {}  # tool_name -> handler

    def add_server(self, name: str, endpoint: str,
                   tools: Optional[list[dict]] = None):
        """
        添加一个 MCP 服务器

        Args:
            name: 服务器名称
            endpoint: 服务器端点 URL
            tools: 服务器提供的工具列表
        """
        self.servers[name] = {
            "endpoint": endpoint,
            "tools": tools or [],
        }

        # 注册工具
        if tools:
            for tool_def in tools:
                tool = MCPTool(
                    name=tool_def["name"],
                    description=tool_def.get("description", ""),
                    server_name=name,
                    parameters=tool_def.get("parameters", {}),
                )
                self.tools[tool.name] = tool

                # 创建一个简单的处理器（实际使用时替换为真实的 MCP 调用）
                self.tool_handlers[tool.name] = self._make_mock_handler(tool)

    def _make_mock_handler(self, tool: MCPTool) -> Callable:
        """创建一个模拟的工具处理器（实际使用时替换为真实的 MCP 调用）"""
        def handler(args: dict[str, Any]) -> str:
            return f"[MCP Tool: {tool.name} from {tool.server_name}] Called with args: {json.dumps(args, ensure_ascii=False)}"
        return handler

    def list_tools(self, server: Optional[str] = None) -> list[MCPTool]:
        """列出所有工具"""
        tools = list(self.tools.values())
        if server:
            tools = [t for t in tools if t.server_name == server]
        return tools

    def get_tool(self, name: str) -> Optional[MCPTool]:
        """获取一个工具"""
        return self.tools.get(name)

    def execute_tool(self, name: str, args: dict[str, Any]) -> Any:
        """执行一个工具"""
        handler = self.tool_handlers.get(name)
        if not handler:
            raise ValueError(f"Tool '{name}' not found")
        return handler(args)

    def get_schemas(self) -> list[dict[str, Any]]:
        """获取所有工具的 schema（OpenAI 格式）"""
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                }
            }
            for t in self.tools.values()
        ]

    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            "servers": len(self.servers),
            "tools": len(self.tools),
            "server_names": list(self.servers.keys()),
        }


# 示例：创建一些模拟的 MCP 服务器
def create_sample_mcp_servers() -> MCPConnector:
    """创建示例 MCP 服务器"""
    connector = MCPConnector()

    # 文件系统 MCP 服务器
    connector.add_server(
        name="filesystem",
        endpoint="http://localhost:3001",
        tools=[
            {
                "name": "read_file",
                "description": "Read a file from the filesystem",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path"}
                    },
                    "required": ["path"],
                },
            },
            {
                "name": "write_file",
                "description": "Write content to a file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "content": {"type": "string"},
                    },
                    "required": ["path", "content"],
                },
            },
        ],
    )

    # GitHub MCP 服务器
    connector.add_server(
        name="github",
        endpoint="http://localhost:3002",
        tools=[
            {
                "name": "create_issue",
                "description": "Create a GitHub issue",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "repo": {"type": "string"},
                        "title": {"type": "string"},
                        "body": {"type": "string"},
                    },
                    "required": ["repo", "title"],
                },
            },
        ],
    )

    return connector
