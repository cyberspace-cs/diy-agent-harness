"""
快速开始示例

演示 DIY Agent Harness 的基本用法。
"""
import asyncio
from typing import Any

from diy_agent_harness.harness import DIYAgentHarness


# 模拟一个 LLM 调用函数（实际使用时替换为真实的 LLM API）
def mock_llm_call(messages: list[dict], tools: list[dict]) -> dict[str, Any]:
    """
    模拟 LLM 响应

    实际使用时，替换为 OpenAI / Anthropic / DeepSeek 等真实 API。
    """
    # 简单的模拟：如果有工具定义，就返回一个工具调用
    if tools and any("calculator" in t.get("function", {}).get("name", "") for t in tools):
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

    # 否则返回最终回答
    return {
        "choices": [{
            "message": {
                "role": "assistant",
                "content": "Hello! This is a mock response from the DIY Agent Harness.",
            }
        }],
        "usage": {"total_tokens": 50},
    }


async def main():
    # 初始化 Harness
    harness = DIYAgentHarness(
        llm_call=mock_llm_call,
        system_prompt="You are a helpful assistant that can use tools to answer questions.",
        storage_dir=".diy-agent-harness",
        enable_rsi=True,
        enable_memory=True,
    )

    print("=== DIY Agent Harness 快速开始 ===\n")

    # 1. 创建新会话
    session = harness.new_session("Demo Session")
    print(f"✅ 创建会话: {session.id}\n")

    # 2. 对话
    print("💬 用户: What is 2 + 2 * 3?")
    result = await harness.chat("What is 2 + 2 * 3?")
    print(f"🤖 Agent: {result.final_message}")
    print(f"📊 步数: {len(result.steps)}")
    print(f"✅ 成功: {result.success}\n")

    # 3. 添加记忆
    harness.add_memory(
        content="用户叫小明，是一个软件工程师",
        category="user_preference",
        importance=0.9,
    )
    print("✅ 添加记忆: 用户叫小明\n")

    # 4. 查看统计
    stats = harness.get_stats()
    print("📊 系统统计:")
    print(f"   会话数: {len(stats['sessions'])}")
    print(f"   工具数: {stats['tools']['total']}")
    if 'memory' in stats:
        print(f"   记忆数: {stats['memory']['total']}")
    if 'rsi' in stats:
        print(f"   RSI 经验数: {stats['rsi']['total_experiences']}")
    print()

    # 5. 列出会话
    print("📋 所有会话:")
    for s in harness.list_sessions():
        print(f"   - {s['id']}: {s['title']} ({s['message_count']} 条消息)")


if __name__ == "__main__":
    asyncio.run(main())
