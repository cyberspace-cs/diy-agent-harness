# DIY Agent Harness

> 从 0 手搓 AI Agent 操作系统

**模型是大脑，Harness 是操作系统。**

这是一个教学项目，从最基础的 Agent Loop 开始，一步步构建一个完整的 AI Agent 操作系统。每个模块都是独立的，可以单独学习。

---

## 🏗️ 架构

```
┌─────────────────────────────────────────┐
│           Skills / Tools                │  ← 应用层：技能和工具
├─────────────────────────────────────────┤
│        Memory / Session                 │  ← 记忆层：短期会话 + 长期记忆
├─────────────────────────────────────────┤
│       Context Management                │  ← 上下文层：压缩、路由、加载
├─────────────────────────────────────────┤
│          Agent Loop                     │  ← 核心层：推理循环
├─────────────────────────────────────────┤
│            LLM Provider                 │  ← 模型层：LLM 调用
└─────────────────────────────────────────┘
```

---

## 📦 模块

| 模块 | 文件 | 说明 |
| --- | --- | --- |
| **Agent Loop** | `core/loop.py` | 最核心的推理循环（while True + tool calling） |
| **Session Manager** | `session/manager.py` | 多会话管理：创建、切换、持久化 |
| **Long-term Memory** | `memory/long_term.py` | 长期记忆：按类别存储和搜索 |
| **Tool Registry** | `tools/registry.py` | 工具系统：注册、发现、执行 |
| **RSI System** | `rsi/system.py` | 递归自改进：从经验中学习 |
| **Harness** | `harness.py` | 主入口：组合所有模块 |

---

## 🚀 快速开始

```python
import asyncio
from diy_agent_harness.harness import DIYAgentHarness

# 定义你的 LLM 调用函数
def my_llm_call(messages, tools):
    # 替换为真实的 LLM API（OpenAI / Anthropic / DeepSeek 等）
    ...

# 初始化 Harness
harness = DIYAgentHarness(
    llm_call=my_llm_call,
    system_prompt="You are a helpful assistant.",
    enable_rsi=True,
    enable_memory=True,
)

# 对话
async def main():
    result = await harness.chat("你好！")
    print(result.final_message)

asyncio.run(main())
```

运行示例：
```bash
python examples/quickstart.py
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
- **Long-term Memory**：跨会话的长期记忆（向量/KV 存储）

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

---

## 📚 学习路线

按照这个顺序学习每个模块：

1. **Agent Loop** (`core/loop.py`) — 理解最基础的推理循环
2. **Tool Registry** (`tools/registry.py`) — 理解工具系统
3. **Session Manager** (`session/manager.py`) — 理解会话管理
4. **Long-term Memory** (`memory/long_term.py`) — 理解记忆系统
5. **RSI System** (`rsi/system.py`) — 理解自改进
6. **Harness** (`harness.py`) — 看怎么把所有模块组合起来

---

## 🔗 参考项目

- [learn-workbuddy](https://github.com/adongwanai/learn-workbuddy) — 24 章桌面 Agent 完整架构
- [learn-claude-code](https://github.com/pyshine/learn-claude-code) — 从 0 构建 CLI Agent
- [Pi](https://pi.dev) — 极简主义编码 Agent
- [ECC](https://github.com/affaan-m/ECC) — Agent Harness 性能优化系统

---

## 📝 License

MIT
