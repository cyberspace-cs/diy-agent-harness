"""
DIY Agent Harness - 测试用例
"""
import asyncio
import json
from typing import Any

import sys
sys.path.insert(0, "/home/user/Doubao/chats/38442034195262978/diy-agent-harness")

from diy_agent_harness.harness import DIYAgentHarness
from diy_agent_harness.core.loop import AgentLoop, Tool
from diy_agent_harness.session.manager import SessionManager
from diy_agent_harness.memory.long_term import LongTermMemory
from diy_agent_harness.tools.registry import ToolRegistry
from diy_agent_harness.rsi.system import RSISystem
from diy_agent_harness.context.compactor import ContextCompactor
from diy_agent_harness.skills.loader import SkillLoader
from diy_agent_harness.mcp.connector import MCPConnector
from diy_agent_harness.rsi.layered_rsi import LayeredRSI


# 模拟 LLM 调用
def mock_llm_call(messages: list[dict], tools: list[dict]) -> dict[str, Any]:
    """模拟 LLM 响应"""
    # 检查是否需要调用工具
    if tools:
        for tool in tools:
            tool_name = tool.get("function", {}).get("name", "")
            if tool_name == "calculator":
                return {
                    "choices": [{
                        "message": {
                            "role": "assistant",
                            "content": "",
                            "tool_calls": [{
                                "id": "call_1",
                                "type": "function",
                                "function": {
                                    "name": "calculator",
                                    "arguments": '{"expression": "2 + 2 * 3"}',
                                }
                            }]
                        }
                    }],
                    "usage": {"total_tokens": 100},
                }

    # 默认返回最终回答
    return {
        "choices": [{
            "message": {
                "role": "assistant",
                "content": "This is a mock response.",
            }
        }],
        "usage": {"total_tokens": 50},
    }


def test_session_manager():
    """测试会话管理器"""
    print("=== 测试 Session Manager ===")
    sm = SessionManager(storage_dir="/tmp/test_sessions")

    # 创建会话
    s1 = sm.create_session("Test 1")
    print(f"✅ 创建会话: {s1.id}")

    # 添加消息
    sm.add_message_to_current("user", "Hello")
    sm.add_message_to_current("assistant", "Hi there!")
    print(f"✅ 添加消息: {len(sm.get_current_session().messages)} 条")

    # 创建第二个会话
    s2 = sm.create_session("Test 2")
    print(f"✅ 第二个会话: {s2.id}")

    # 切换会话
    sm.switch_session(s1.id)
    print(f"✅ 切换会话: {sm.get_current_session().title}")

    # 列出所有会话
    sessions = sm.list_sessions()
    print(f"✅ 所有会话: {len(sessions)} 个")

    print()


def test_memory():
    """测试记忆系统"""
    print("=== 测试 Long-term Memory ===")
    mem = LongTermMemory(storage_dir="/tmp/test_memory")

    # 添加记忆
    mem.add("用户叫小明", category="user_preference", importance=0.9)
    mem.add("用户喜欢 Python", category="user_preference", importance=0.8)
    mem.add("用户是软件工程师", category="user_preference", importance=0.7)
    print("✅ 添加 3 条记忆")

    # 搜索记忆
    results = mem.search(query="Python")
    print(f"✅ 搜索 'Python': {len(results)} 条结果")

    # 获取 prompt 补充
    prompt_add = mem.get_relevant_for_prompt("Python programming")
    print(f"✅ Prompt 补充: {len(prompt_add)} 字符")

    # 统计
    stats = mem.get_stats()
    print(f"✅ 统计: {stats['total']} 条记忆, 平均重要性 {stats['avg_importance']:.2f}")

    print()


def test_tools():
    """测试工具系统"""
    print("=== 测试 Tool Registry ===")
    reg = ToolRegistry()

    # 注册工具
    from diy_agent_harness.tools.registry import ToolDefinition
    reg.register(ToolDefinition(
        name="test_tool",
        description="A test tool",
        parameters={"type": "object", "properties": {"x": {"type": "number"}}},
        handler=lambda args: args["x"] * 2,
        category="test",
    ))
    print("✅ 注册工具")

    # 执行工具
    result = reg.execute("test_tool", {"x": 21})
    print(f"✅ 执行工具: 21 * 2 = {result}")

    # 获取 schema
    schemas = reg.get_schemas()
    print(f"✅ Schema 数量: {len(schemas)}")

    print()


def test_rsi():
    """测试 RSI 系统"""
    print("=== 测试 RSI System ===")
    rsi = RSISystem(storage_dir="/tmp/test_rsi")

    # 记录经验
    rsi.record_experience(
        task="写 Python 代码",
        context="",
        action="",
        outcome="成功",
        success=True,
        lesson="Python 代码要注意缩进",
    )
    print("✅ 记录经验")

    # 获取相关教训
    lessons = rsi.get_relevant_lessons("Python 编程")
    print(f"✅ 相关教训: {len(lessons)} 条")

    # 构建 prompt 补充
    prompt_add = rsi.build_system_prompt_addition("Python 编程")
    print(f"✅ Prompt 补充: {len(prompt_add)} 字符")

    # 统计
    stats = rsi.get_stats()
    print(f"✅ 统计: {stats['total_experiences']} 条经验, 成功率 {stats['success_rate']:.1%}")

    print()


def test_layered_rsi():
    """测试分层 RSI"""
    print("=== 测试 Layered RSI ===")
    lrsi = LayeredRSI(storage_dir="/tmp/test_layered_rsi")

    # 记录各层经验
    lrsi.record_experience(
        layer="memory",
        operation="retrieval",
        input_data={"query": "Python"},
        output_data={"results": 5},
        success=True,
        feedback_score=0.9,
    )
    print("✅ 记录 memory 层经验")

    lrsi.record_experience(
        layer="skills",
        operation="matching",
        input_data={"query": "代码 review"},
        output_data={"matched": ["code-review"]},
        success=True,
        feedback_score=0.8,
    )
    print("✅ 记录 skills 层经验")

    lrsi.record_experience(
        layer="tools",
        operation="execution",
        input_data={"tool": "calculator"},
        output_data={"result": "8"},
        success=True,
        feedback_score=1.0,
    )
    print("✅ 记录 tools 层经验")

    # 获取各层策略
    strategies = lrsi.get_all_strategies()
    print(f"✅ 各层策略: {len(strategies)} 层")

    # 生成报告
    report = lrsi.get_summary_report()
    print(f"✅ 总结报告: {len(report)} 字符")

    print()


def test_compaction():
    """测试上下文压缩"""
    print("=== 测试 Context Compaction ===")
    compactor = ContextCompactor(max_messages=10, keep_recent=4)

    # 生成一堆消息
    messages = [{"role": "system", "content": "You are helpful."}]
    for i in range(15):
        messages.append({"role": "user", "content": f"Question {i}"})
        messages.append({"role": "assistant", "content": f"Answer {i}"})

    print(f"原始消息数: {len(messages)}")

    # 判断是否需要压缩
    needs = compactor.should_compact(messages)
    print(f"需要压缩: {needs}")

    # 执行压缩
    compacted, result = compactor.compact(messages)
    print(f"压缩后消息数: {len(compacted)}")
    print(f"节省 token: {result.tokens_saved}")

    print()


def test_skills():
    """测试技能系统"""
    print("=== 测试 Skills Loader ===")
    loader = SkillLoader()

    # 列出技能
    skills = loader.list_skills()
    print(f"✅ 内置技能: {len(skills)} 个")
    for s in skills:
        print(f"   - {s['name']}: {s['description'][:50]}...")

    # 匹配技能
    matched = loader.match_skills("帮我写个 Python 函数")
    print(f"✅ 匹配 'Python 函数': {len(matched)} 个技能")

    # 构建 prompt
    prompt_add, tools = loader.build_skills_prompt("帮我 review 这段代码")
    print(f"✅ Prompt 补充: {len(prompt_add)} 字符")

    print()


def test_mcp():
    """测试 MCP 连接器"""
    print("=== 测试 MCP Connector ===")
    connector = MCPConnector()

    # 添加服务器
    connector.add_server(
        name="filesystem",
        endpoint="http://localhost:3001",
        tools=[
            {
                "name": "read_file",
                "description": "Read a file",
                "parameters": {"type": "object", "properties": {"path": {"type": "string"}}},
            }
        ],
    )
    print("✅ 添加 MCP 服务器")

    # 列出工具
    tools = connector.list_tools()
    print(f"✅ 工具数量: {len(tools)}")

    # 执行工具
    result = connector.execute_tool("read_file", {"path": "/tmp/test.txt"})
    print(f"✅ 执行工具: {result[:50]}...")

    print()


async def test_full_harness():
    """测试完整 Harness"""
    print("=== 测试完整 DIY Agent Harness ===")

    harness = DIYAgentHarness(
        llm_call=mock_llm_call,
        system_prompt="You are a helpful assistant.",
        storage_dir="/tmp/test_harness",
        enable_rsi=True,
        enable_memory=True,
        enable_compaction=True,
        enable_skills=True,
        enable_mcp=False,
    )

    # 创建会话
    session = harness.new_session("Test Session")
    print(f"✅ 创建会话: {session.id}")

    # 对话
    result = await harness.chat("What is 2 + 2 * 3?")
    print(f"✅ 对话完成: {len(result.steps)} 步, 成功={result.success}")

    # 添加记忆
    harness.add_memory("用户喜欢 Python", category="user_preference", importance=0.9)
    print("✅ 添加记忆")

    # 获取统计
    stats = harness.get_stats()
    print(f"✅ 统计:")
    print(f"   - 会话: {len(stats['sessions'])}")
    print(f"   - 工具: {stats['tools']['total']}")
    print(f"   - 记忆: {stats['memory']['total']}")
    print(f"   - RSI 经验: {stats['rsi']['total_experiences']}")
    print(f"   - 技能: {stats['skills']['total']}")

    print()


if __name__ == "__main__":
    # 运行所有测试
    test_session_manager()
    test_memory()
    test_tools()
    test_rsi()
    test_layered_rsi()
    test_compaction()
    test_skills()
    test_mcp()
    asyncio.run(test_full_harness())

    print("=" * 50)
    print("✅ 所有测试通过！")
