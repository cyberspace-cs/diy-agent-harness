# DIY Agent Harness

> 从 0 手搓 AI Agent 操作系统

**模型是大脑，Harness 是操作系统。**

这是一个教学项目，从最基础的 Agent Loop 开始，一步步构建一个完整的 AI Agent 操作系统。每个模块都是独立的，可以单独学习。

---

## 🏗️ 架构

```
┌─────────────────────────────────────────────┐
│           Skills / Tools / MCP           │  ← 应用层：技能、工具、外部连接
├─────────────────────────────────────────────┤
│        Memory / Session / RSI            │  ← 记忆层：短期会话 + 长期记忆 + 自改进
├─────────────────────────────────────────────┤
│       Context Management (Compaction)     │  ← 上下文层：压缩、路由、加载
├─────────────────────────────────────────────┤
│          Agent Loop                      │  ← 核心层：推理循环
├─────────────────────────────────────────────┤
│            LLM Provider                  │  ← 模型层：LLM 调用
└─────────────────────────────────────────────┘
```

---

## 📦 模块总览

| 模块 | 文件 | 说明 | 输入 | 输出 |
| --- | --- | --- | --- | --- |
| **Agent Loop** | `core/loop.py` | 核心推理循环 | 用户消息 + 工具列表 | Agent 执行结果 |
| **Session Manager** | `session/manager.py` | 多会话管理 | 会话 ID / 标题 | 会话对象 |
| **Long-term Memory** | `memory/long_term.py` | 长期记忆 | 内容 + 类别 + 重要性 | 记忆条目 |
| **Tool Registry** | `tools/registry.py` | 工具系统 | 工具定义 + 参数 | 执行结果 |
| **RSI System** | `rsi/system.py` | 递归自改进 | 任务 + 结果 + 教训 | 经验记录 |
| **Context Compactor** | `context/compactor.py` | 上下文压缩 | 消息历史 | 压缩后的消息 |
| **Skills Loader** | `skills/loader.py` | 技能加载 | 用户输入 | 匹配的技能 |
| **MCP Connector** | `mcp/connector.py` | MCP 连接 | 服务器配置 + 工具调用 | 远程工具结果 |
| **Harness** | `harness.py` | 主入口 | 用户消息 | 完整对话结果 |

---

## 🚀 快速开始

### 安装

```bash
git clone https://github.com/cyberspace-cs/diy-agent-harness.git
cd diy-agent-harness
pip install -r requirements.txt  # 暂时无依赖，纯 Python
```

### 最小示例

```python
import asyncio
from diy_agent_harness.harness import DIYAgentHarness

# 1. 定义你的 LLM 调用函数
def my_llm_call(messages: list[dict], tools: list[dict]) -> dict:
    """
    你的 LLM 调用函数
    
    输入：
    - messages: 对话历史（OpenAI 格式）
    - tools: 可用工具列表（OpenAI function calling 格式）
    
    输出：OpenAI 格式的响应
    """
    # 替换为真实的 LLM API（OpenAI / Anthropic / DeepSeek 等）
    return {
        "choices": [{
            "message": {
                "role": "assistant",
                "content": "Hello! How can I help you?",
            }
        }],
        "usage": {"total_tokens": 100},
    }

# 2. 初始化 Harness
harness = DIYAgentHarness(
    llm_call=my_llm_call,
    system_prompt="You are a helpful assistant.",
    enable_rsi=True,
    enable_memory=True,
)

# 3. 对话
async def main():
    result = await harness.chat("你好！")
    print(result.final_message)

asyncio.run(main())
```

---

## 📝 输入输出示例

### 示例 1：Agent Loop（工具调用）

**输入：**
```python
user_message = "What is 2 + 2 * 3?"
tools = [{"name": "calculator", "description": "Evaluate math expressions"}]
```

**输出：**
```
Step 1: LLM decides to call calculator
Step 2: Tool returns "8"
Step 3: LLM gives final answer: "The answer is 8."
```

**AgentResult：**
```python
AgentResult(
    success=True,
    final_message="The answer is 8.",
    steps=[
        {"step": 1, "has_tool_calls": True},
        {"step": 2, "has_tool_calls": False},
    ],
    total_tokens=150,
)
```

---

### 示例 2：Session Manager（多会话）

**输入：**
```python
sm.create_session("Python Learning")
sm.add_message_to_current("user", "How do I read a file?")
sm.switch_session("sess_xxx")
sm.add_message_to_current("user", "What is machine learning?")
```

**输出：**
```python
# 列出所有会话
[
    {"id": "sess_1", "title": "Python Learning", "message_count": 2},
    {"id": "sess_2", "title": "ML Discussion", "message_count": 2},
]
```

---

### 示例 3：Long-term Memory（记忆搜索）

**输入：**
```python
memory.add("用户叫小明，是软件工程师", category="user_preference", importance=0.9)
memory.add("用户喜欢 Python", category="user_preference", importance=0.8)

# 搜索
results = memory.search(query="Python")
```

**输出：**
```python
# 相关记忆
[
    MemoryItem(
        content="用户喜欢 Python",
        category="user_preference",
        importance=0.8,
    ),
]

# 注入到 system prompt 的格式
"Relevant memories:
 - [user_preference] 用户喜欢 Python"
```

---

### 示例 4：RSI System（自改进）

**输入：**
```python
rsi.record_experience(
    task="写 Python 代码",
    outcome="成功",
    success=True,
    lesson="Python 代码要注意缩进",
)

# 下次执行类似任务
lessons = rsi.build_system_prompt_addition("Python 编程")
```

**输出：**
```
Lessons learned from previous experiences:
1. Python 代码要注意缩进
```

---

### 示例 5：Context Compaction（上下文压缩）

**输入：**
```python
# 31 条消息（太长了）
messages = [system_msg] + 30 条对话消息

compactor = ContextCompactor(max_messages=10, keep_recent=4)
compacted, result = compactor.compact(messages)
```

**输出：**
```
原始消息数: 31
压缩后消息数: 6
节省 token: 25

压缩后：
[system_msg] + [summary_msg] + [最近 4 条消息]
```

---

### 示例 6：Skills Loader（技能加载）

**输入：**
```python
user_input = "帮我 review 这段代码有没有 bug"

loader = SkillLoader()
skills_prompt, tools = loader.build_skills_prompt(user_input)
```

**输出：**
```
Relevant skills activated:

[code-review]
You are a senior code reviewer. When reviewing code:
1. Check for correctness bugs
2. Check for security issues
...
```

---

### 示例 7：MCP Connector（外部连接）

**输入：**
```python
connector = MCPConnector()
connector.add_server(
    name="filesystem",
    endpoint="http://localhost:3001",
    tools=[{"name": "read_file", "description": "Read a file"}],
)

result = connector.execute_tool("read_file", {"path": "/tmp/test.txt"})
```

**输出：**
```
"[MCP Tool: read_file from filesystem] Called with args: {"path": "/tmp/test.txt"}"
```

---

## 🎯 核心概念

### 1. Agent Loop
最基础的推理循环：
1. 把 system prompt + 历史消息 + 工具定义发给 LLM
2. LLM 返回最终回答，或工具调用
3. 执行工具，把结果加回消息历史
4. 重复直到完成

### 2. Session Management
多会话管理：
- 创建新会话
- 切换会话
- 会话持久化到磁盘
- 每个会话有独立的消息历史

### 3. Memory System
两层记忆：
- **Working Memory**：当前会话的工作记忆（短期）
- **Long-term Memory**：跨会话的长期记忆（关键词搜索 → 可扩展为向量搜索）

### 4. Tool System
工具系统：
- 注册工具
- 工具 schema 自动转换为 OpenAI 格式
- 按类别过滤工具

### 5. RSI (Recursive Self-Improvement)
递归自改进：
- 记录每次任务执行的经验
- 从成功和失败中提炼教训
- 把相关教训注入到 system prompt
- 让 Agent 下次做得更好

### 6. Context Compaction
上下文压缩：
- 保留 system 消息
- 保留最近 N 条消息
- 中间的旧消息压缩成摘要

### 7. Skills System
技能加载：
- 预定义的提示词包
- 根据用户输入自动匹配
- 注入到 system prompt

### 8. MCP Connectors
外部连接：
- 连接到外部 MCP 服务器
- 发现和调用远程工具
- 统一的工具接口

---

## 🧪 运行测试

```bash
python tests/test_all.py
```

输出：
```
=== 测试 Session Manager ===
✅ 创建会话
✅ 添加消息
✅ 切换会话

=== 测试 Long-term Memory ===
✅ 添加记忆
✅ 搜索记忆

=== 测试 Tool Registry ===
✅ 注册工具
✅ 执行工具

=== 测试 RSI System ===
✅ 记录经验
✅ 获取教训

...

✅ 所有测试通过！
```

---

## 📚 学习路线

按照这个顺序学习每个模块：

1. **Agent Loop** (`core/loop.py`) — 理解最基础的推理循环
2. **Tool Registry** (`tools/registry.py`) — 理解工具系统
3. **Session Manager** (`session/manager.py`) — 理解会话管理
4. **Long-term Memory** (`memory/long_term.py`) — 理解记忆系统
5. **RSI System** (`rsi/system.py`) — 理解自改进
6. **Context Compactor** (`context/compactor.py`) — 理解上下文压缩
7. **Skills Loader** (`skills/loader.py`) — 理解技能加载
8. **MCP Connector** (`mcp/connector.py`) — 理解外部连接
9. **Harness** (`harness.py`) — 看怎么把所有模块组合起来

---

## 🔗 参考项目

- [learn-workbuddy](https://github.com/adongwanai/learn-workbuddy) — 24 章桌面 Agent 完整架构
- [learn-claude-code](https://github.com/pyshine/learn-claude-code) — 从 0 构建 CLI Agent
- [Pi](https://pi.dev) — 极简主义编码 Agent
- [ECC](https://github.com/affaan-m/ECC) — Agent Harness 性能优化系统

---

## 📝 License

MIT
