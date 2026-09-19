# DIY Agent Harness

> 从 0 手搓 AI Agent 操作系统

**模型是大脑，Harness 是操作系统。**

这是一个教学项目，从最基础的 Agent Loop 开始，一步步构建一个完整的 AI Agent 操作系统。每个模块都是独立的，可以单独学习。

参考综述：[Code as Agent Harness](https://arxiv.org/abs/2605.18747)

---

## 🏗️ 架构

```
┌─────────────────────────────────────────────┐
│     Planning / Feedback / Skills / Tools    │  ← 应用层：规划、反馈、技能、工具
├─────────────────────────────────────────────┤
│  Memory / Session / RSI / Layered RSI     │  ← 记忆层：短期会话 + 长期记忆 + 自改进
├─────────────────────────────────────────────┤
│       Context Management (Compaction)       │  ← 上下文层：压缩、路由、加载
├─────────────────────────────────────────────┤
│          Agent Loop                        │  ← 核心层：推理循环
├─────────────────────────────────────────────┤
│            LLM Provider                    │  ← 模型层：LLM 调用
└─────────────────────────────────────────────┘
```

---

## 📦 模块总览

| # | 模块 | 文件 | 说明 | 输入 | 输出 |
| --- | --- | --- | --- | --- | --- |
| 1 | **Agent Loop** | `core/loop.py` | 核心推理循环 | 用户消息 + 工具列表 | Agent 执行结果 |
| 2 | **Session Manager** | `session/manager.py` | 多会话管理 | 会话 ID / 标题 | 会话对象 |
| 3 | **Long-term Memory** | `memory/long_term.py` | 长期记忆 | 内容 + 类别 + 重要性 | 记忆条目 |
| 4 | **Tool Registry** | `tools/registry.py` | 工具系统 | 工具定义 + 参数 | 执行结果 |
| 5 | **RSI System** | `rsi/system.py` | 全局递归自改进 | 任务 + 结果 + 教训 | 经验记录 |
| 6 | **Layered RSI** | `rsi/layered_rsi.py` | 分层自改进 | 各层执行经验 | 各层优化策略 |
| 7 | **Context Compactor** | `context/compactor.py` | 上下文压缩 | 消息历史 | 压缩后的消息 |
| 8 | **Skills Loader** | `skills/loader.py` | 技能加载 | 用户输入 | 匹配的技能 |
| 9 | **MCP Connector** | `mcp/connector.py` | MCP 外部连接 | 服务器配置 + 工具调用 | 远程工具结果 |
| 10 | **Planning System** | `planning/system.py` | 规划系统 | 任务 + 步骤描述 | 计划对象 |
| 11 | **Feedback Loop** | `feedback/loop.py` | 反馈循环 | 执行结果 + 洞察 | 优化反馈 |
| - | **Harness** | `harness.py` | 主入口 | 用户消息 | 完整对话结果 |

---

## 🚀 快速开始

### 安装

```bash
git clone https://github.com/cyberspace-cs/diy-agent-harness.git
cd diy-agent-harness
# 暂时无依赖，纯 Python
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

## 📝 各模块核心代码详解

### 1. Agent Loop（核心推理循环）

**文件**：`diy_agent_harness/core/loop.py`

**作用**：Agent 的心脏，不断调用 LLM → 执行工具 → 再调用 LLM，直到完成任务。

**核心代码**：

```python
class AgentLoop:
    async def run(self, user_message: str) -> AgentResult:
        """
        核心推理循环：
        1. 把用户消息加入对话
        2. 调用 LLM
        3. 如果 LLM 要调用工具 → 执行工具 → 回到步骤 2
        4. 如果 LLM 给出最终答案 → 返回结果
        """
        self.messages.append({"role": "user", "content": user_message})
        
        for step in range(self.max_steps):
            # 调用 LLM
            response = self.llm_call(self.messages, self.tool_schemas)
            message = response["choices"][0]["message"]
            
            # 检查是否要调用工具
            if message.get("tool_calls"):
                # 执行每个工具调用
                for tool_call in message["tool_calls"]:
                    result = self._execute_tool(tool_call)
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": result,
                    })
            else:
                # 没有工具调用，说明给出了最终答案
                return AgentResult(
                    success=True,
                    final_message=message["content"],
                    steps=step + 1,
                )
        
        return AgentResult(success=False, final_message="Max steps reached.")
```

**输入**：用户消息字符串
**输出**：`AgentResult` 对象（包含最终答案、步数、是否成功）

---

### 2. Session Manager（多会话管理）

**文件**：`diy_agent_harness/session/manager.py`

**作用**：管理多个对话会话，支持创建、切换、持久化。

**核心代码**：

```python
class SessionManager:
    def create_session(self, title: str = None) -> Session:
        """创建新会话"""
        session_id = f"sess_{uuid.uuid4().hex[:8]}"
        session = Session(
            id=session_id,
            title=title or f"Session {len(self.sessions) + 1}",
            messages=[],
            created_at=datetime.now(),
        )
        self.sessions[session_id] = session
        self.current_session_id = session_id
        self._save_to_disk()
        return session

    def switch_session(self, session_id: str) -> bool:
        """切换到指定会话"""
        if session_id in self.sessions:
            self.current_session_id = session_id
            self._save_to_disk()
            return True
        return False
```

**输入**：会话标题
**输出**：`Session` 对象（包含会话 ID、消息列表、创建时间）

---

### 3. Long-term Memory（长期记忆）

**文件**：`diy_agent_harness/memory/long_term.py`

**作用**：长期存储重要信息，支持关键词搜索，自动注入到 prompt。

**核心代码**：

```python
class LongTermMemory:
    def add(self, content: str, category: str = "general", importance: float = 0.5):
        """添加记忆"""
        memory = MemoryItem(
            id=uuid.uuid4().hex[:8],
            content=content,
            category=category,
            importance=importance,
            timestamp=datetime.now(),
        )
        self.items.append(memory)
        self._save_to_disk()

    def search(self, query: str, limit: int = 5) -> list[MemoryItem]:
        """关键词搜索记忆"""
        query_lower = query.lower()
        results = []
        for item in self.items:
            if query_lower in item.content.lower():
                results.append(item)
        # 按重要性排序
        results.sort(key=lambda x: x.importance, reverse=True)
        return results[:limit]
```

**输入**：记忆内容 + 类别 + 重要性
**输出**：记忆条目对象

---

### 4. Tool Registry（工具系统）

**文件**：`diy_agent_harness/tools/registry.py`

**作用**：注册和管理工具，自动转换为 OpenAI function calling 格式。

**核心代码**：

```python
class ToolRegistry:
    def register(self, tool: Tool):
        """注册工具"""
        self.tools[tool.name] = tool

    def to_openai_schemas(self) -> list[dict]:
        """转换为 OpenAI function calling 格式"""
        schemas = []
        for tool in self.tools.values():
            schemas.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                }
            })
        return schemas

    async def execute(self, name: str, params: dict) -> str:
        """执行工具"""
        tool = self.tools.get(name)
        if not tool:
            return f"Error: Tool {name} not found."
        return await tool.handler(**params)
```

**输入**：工具定义 + 参数字典
**输出**：工具执行结果字符串

---

### 5. RSI System（递归自改进）

**文件**：`diy_agent_harness/rsi/system.py`

**作用**：记录每次任务执行的经验，从成功和失败中学习，把教训注入到下次的 prompt 里。

**核心代码**：

```python
class RSISystem:
    def record_experience(self, task: str, outcome: str, success: bool, lesson: str = ""):
        """记录一次执行经验"""
        experience = Experience(
            task=task,
            outcome=outcome,
            success=success,
            lesson=lesson,
            timestamp=datetime.now(),
        )
        self.experiences.append(experience)
        self._save_to_disk()

    def build_system_prompt_addition(self, task: str) -> str:
        """构建注入到 system prompt 的补充内容"""
        # 找和当前任务相关的经验
        relevant = self._find_relevant(task)
        if not relevant:
            return ""
        
        lines = ["", "Lessons learned from previous experiences:"]
        for exp in relevant[-3:]:  # 最近 3 条
            icon = "✅" if exp.success else "❌"
            lines.append(f"{icon} {exp.lesson or exp.outcome}")
        return "\n".join(lines)
```

**输入**：任务描述 + 执行结果 + 教训
**输出**：经验记录 + 注入到 prompt 的补充文本

---

### 6. Layered RSI（分层自改进）

**文件**：`diy_agent_harness/rsi/layered_rsi.py`

**作用**：让 Harness 的每一层（Memory、Skills、Tools、Context）都能从经验中学习和改进。

**核心代码**：

```python
class LayeredRSI:
    def record_experience(
        self,
        layer: str,  # memory / skills / tools / context
        operation: str,
        input_data: dict,
        output_data: dict,
        success: bool,
        feedback_score: float,
    ):
        """记录某一层的经验"""
        exp = LayerExperience(
            layer=layer,
            operation=operation,
            input_data=input_data,
            output_data=output_data,
            success=success,
            feedback_score=feedback_score,
        )
        self.experiences[layer].append(exp)
        self._update_layer_stats(layer)

    def get_layer_strategy(self, layer: str) -> dict:
        """获取某一层的优化策略"""
        stats = self.layer_stats.get(layer, {})
        return {
            "total_experiences": stats.get("total", 0),
            "success_rate": stats.get("success_rate", 0.5),
            "recommendations": self._generate_recommendations(layer),
        }
```

**输入**：层名 + 操作 + 输入输出数据 + 成功/失败 + 反馈分数
**输出**：各层的优化策略建议

---

### 7. Context Compactor（上下文压缩）

**文件**：`diy_agent_harness/context/compactor.py`

**作用**：当对话太长时，自动压缩旧消息，保留 system prompt 和最近的消息。

**核心代码**：

```python
class ContextCompactor:
    def should_compact(self, messages: list[dict]) -> bool:
        """判断是否需要压缩"""
        return len(messages) > self.max_messages

    def compact(self, messages: list[dict]) -> tuple[list[dict], CompactionResult]:
        """压缩消息历史"""
        # 1. 保留 system 消息
        system_msgs = [m for m in messages if m["role"] == "system"]
        
        # 2. 保留最近 N 条消息
        recent_msgs = messages[-self.keep_recent:]
        
        # 3. 中间的旧消息压缩成摘要
        old_msgs = messages[len(system_msgs):-self.keep_recent]
        summary = self._summarize(old_msgs)
        
        # 4. 组合起来
        compacted = system_msgs + [
            {"role": "system", "content": f"Earlier conversation summary: {summary}"}
        ] + recent_msgs
        
        return compacted, CompactionResult(
            original=len(messages),
            compacted=len(compacted),
            saved_tokens=len(messages) - len(compacted),
        )
```

**输入**：完整的消息历史
**输出**：压缩后的消息列表 + 压缩结果统计

---

### 8. Skills Loader（技能加载）

**文件**：`diy_agent_harness/skills/loader.py`

**作用**：根据用户输入，自动匹配最合适的技能，把技能的提示词注入到 system prompt。

**核心代码**：

```python
class SkillLoader:
    def match_skills(self, user_input: str, limit: int = 3) -> list[Skill]:
        """根据用户输入匹配技能"""
        input_lower = user_input.lower()
        scores = []
        
        for skill in self.skills.values():
            score = 0
            # 计算关键词匹配分数
            for keyword in skill.keywords:
                if keyword.lower() in input_lower:
                    score += 1
            if score > 0:
                scores.append((score, skill))
        
        # 按分数排序
        scores.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in scores[:limit]]

    def build_prompt_addition(self, matched_skills: list[Skill]) -> str:
        """构建注入到 system prompt 的技能内容"""
        if not matched_skills:
            return ""
        
        lines = ["", "Relevant skills to use:"]
        for skill in matched_skills:
            lines.append(f"- {skill.name}: {skill.prompt_template}")
        return "\n".join(lines)
```

**输入**：用户输入文本
**输出**：匹配到的技能列表 + 注入到 prompt 的内容

---

### 9. MCP Connector（MCP 外部连接）

**文件**：`diy_agent_harness/mcp/connector.py`

**作用**：连接外部 MCP（Model Context Protocol）服务器，发现和调用远程工具。

**核心代码**：

```python
class MCPConnector:
    def add_server(self, name: str, url: str):
        """添加 MCP 服务器"""
        self.servers[name] = MCPServer(name=name, url=url)

    def list_tools(self) -> list[dict]:
        """列出所有服务器上的工具"""
        all_tools = []
        for server in self.servers.values():
            tools = self._fetch_server_tools(server)
            all_tools.extend(tools)
        return all_tools

    async def execute_tool(self, tool_name: str, params: dict) -> str:
        """执行远程工具"""
        # 找到工具所在的服务器
        server = self._find_tool_server(tool_name)
        if not server:
            return f"Error: Tool {tool_name} not found on any server."
        
        # 调用远程工具
        return await self._call_remote_tool(server, tool_name, params)
```

**输入**：MCP 服务器地址 + 工具调用参数
**输出**：远程工具执行结果

---

### 10. Planning System（规划系统）

**文件**：`diy_agent_harness/planning/system.py`

**作用**：把复杂任务拆成多个步骤，支持步骤依赖，追踪进度。

**核心代码**：

```python
class PlanningSystem:
    def create_plan(self, task: str, step_descriptions: list[str]) -> Plan:
        """创建新计划"""
        plan_id = f"plan_{uuid.uuid4().hex[:8]}"
        steps = []
        
        for i, desc in enumerate(step_descriptions):
            step = PlanStep(
                step_id=f"step_{i+1}",
                description=desc,
                depends_on=[f"step_{i}"] if i > 0 else [],  # 默认串行
            )
            steps.append(step)
        
        plan = Plan(
            plan_id=plan_id,
            task=task,
            steps=steps,
            status=StepStatus.IN_PROGRESS,
        )
        self.plans[plan_id] = plan
        return plan

    def get_next_steps(self) -> list[PlanStep]:
        """获取下一步要执行的步骤（依赖都完成了的）"""
        completed_ids = {s.step_id for s in self.current_plan.steps 
                         if s.status == StepStatus.COMPLETED}
        pending = []
        for step in self.current_plan.steps:
            if step.status == StepStatus.PENDING:
                if all(dep in completed_ids for dep in step.depends_on):
                    pending.append(step)
        return pending
```

**输入**：任务描述 + 步骤描述列表
**输出**：`Plan` 对象（包含步骤列表、状态、进度）

---

### 11. Feedback Loop（反馈循环）

**文件**：`diy_agent_harness/feedback/loop.py`

**作用**：从每次执行中学习，记录成功/失败，把经验注入到下次的执行中。

**核心代码**：

```python
class FeedbackLoop:
    def record_success(self, context: str, insight: str, action: str = ""):
        """记录成功经验"""
        fb = Feedback(
            feedback_id=f"fb_{uuid.uuid4().hex[:8]}",
            feedback_type=FeedbackType.SUCCESS,
            context=context,
            insight=insight,
            action=action or "Keep doing what works.",
        )
        self.feedbacks.append(fb)

    def build_prompt_addition(self, task: str) -> str:
        """构建注入到 system prompt 的反馈内容"""
        relevant = self.get_relevant_feedback(task, limit=3)
        if not relevant:
            return ""
        
        lines = ["", "Lessons learned from previous experiences:"]
        for fb in relevant:
            icon = "✅" if fb.feedback_type == FeedbackType.SUCCESS else "❌"
            lines.append(f"{icon} {fb.insight}")
            if fb.action:
                lines.append(f"   Action: {fb.action}")
        return "\n".join(lines)
```

**输入**：执行场景 + 学到的洞察 + 下次怎么做
**输出**：相关反馈 + 注入到 prompt 的优化建议

---

## 🎯 完整实战例子：做一个编程助手

让我们用一个完整的场景，把所有模块串起来看看：

### 场景：用户说"帮我写一个 Python 函数，计算斐波那契数列，然后测试一下"

---

#### 第 1 步：Skills Loader 匹配技能

**输入**：用户消息
```python
user_message = "帮我写一个 Python 函数，计算斐波那契数列，然后测试一下"
```

**Skills Loader 做了什么**：
```python
matched_skills = skill_loader.match_skills(user_message)
# 匹配到的技能：
# 1. code-review (关键词: "Python", "函数")
# 2. writing-assistant (关键词: "帮我写")
```

**输出**：注入到 system prompt 的内容
```
Relevant skills to use:
- code-review: Review code for quality, bugs, and best practices.
  Always check for edge cases, performance, and readability.
```

---

#### 第 2 步：Memory 注入相关记忆

**输入**：用户消息 + 历史记忆
```python
relevant_memories = memory.search(user_message)
# 假设之前用户说过"我喜欢用类型提示"
# 记忆条目：
# - content: "用户喜欢用 Python 类型提示"
#   category: "user_preference"
#   importance: 0.9
```

**输出**：注入到 system prompt 的内容
```
Relevant memories from user:
- 用户喜欢用 Python 类型提示
```

---

#### 第 3 步：RSI 注入之前的教训

**输入**：当前任务
```python
prompt_addition = rsi.build_system_prompt_addition("Python 代码")
# 假设之前的经验：
# - ❌ 失败: 斐波那契递归会栈溢出
#   教训: "斐波那契数列要用迭代实现，不要递归"
```

**输出**：注入到 system prompt 的内容
```
Lessons learned from previous experiences:
1. ❌ 斐波那契数列要用迭代实现，不要递归
```

---

#### 第 4 步：Agent Loop 开始执行

**组装好的 system prompt**：
```
You are a helpful assistant.

Relevant skills to use:
- code-review: Review code for quality, bugs, and best practices.

Relevant memories from user:
- 用户喜欢用 Python 类型提示

Lessons learned from previous experiences:
1. ❌ 斐波那契数列要用迭代实现，不要递归
```

**执行过程**：

**Step 1**: LLM 思考后说：
```python
{
    "role": "assistant",
    "content": "我来帮你写一个斐波那契函数，用迭代实现，加上类型提示，然后写测试。",
    "tool_calls": [
        {
            "id": "call_1",
            "function": {
                "name": "write_file",
                "arguments": '{"path": "fib.py", "content": "def fibonacci(n: int) -> list[int]:..."}'
            }
        }
    ]
}
```

**Step 2**: 执行工具
```python
tool_result = "File written successfully: fib.py"
```

**Step 3**: LLM 又说：
```python
{
    "role": "assistant",
    "content": "现在我来写测试。",
    "tool_calls": [
        {
            "id": "call_2",
            "function": {
                "name": "write_file",
                "arguments": '{"path": "test_fib.py", "content": "def test_fibonacci():..."}'
            }
        }
    ]
}
```

**Step 4**: 执行工具
```python
tool_result = "File written successfully: test_fib.py"
```

**Step 5**: LLM 最终回答：
```python
{
    "role": "assistant",
    "content": "完成了！我写了：\n1. fib.py - 斐波那契函数（迭代实现，带类型提示）\n2. test_fib.py - 测试用例\n\n你可以运行 `python test_fib.py` 来测试。"
}
```

---

#### 第 5 步：Feedback Loop 记录经验

**执行完成后**：
```python
feedback.record_success(
    context="Python 函数编写",
    insight="带类型提示的斐波那契函数一次通过测试",
    action="继续用迭代实现 + 类型提示的风格",
)
```

**下次用户再写 Python 代码时**，这个经验会自动注入到 prompt 里。

---

#### 第 6 步：Layered RSI 记录各层经验

```python
# Memory 层
layered_rsi.record_experience(
    layer="memory",
    operation="retrieval",
    input_data={"query": "Python 函数"},
    output_data={"relevant": 1},
    success=True,
    feedback_score=0.9,
)

# Skills 层
layered_rsi.record_experience(
    layer="skills",
    operation="matching",
    input_data={"query": "Python 函数"},
    output_data={"matched": ["code-review"]},
    success=True,
    feedback_score=0.8,
)

# Tools 层
layered_rsi.record_experience(
    layer="tools",
    operation="execution",
    input_data={"steps": 2},
    output_data={"success": True},
    success=True,
    feedback_score=0.95,
)
```

---

#### 第 7 步：Planning System 追踪进度

如果是更复杂的任务，比如"做一个完整的 Web 应用"：

```python
plan = planning.create_plan(
    task="Build a todo web app",
    step_descriptions=[
        "Design the UI",
        "Setup project structure",
        "Implement backend API",
        "Implement frontend",
        "Write tests",
        "Deploy",
    ],
)

# 每完成一步就更新状态
planning.start_step("step_1")
planning.complete_step("step_1", "UI design done")

# 查看进度
print(planning.get_plan_summary())
# Plan: Build a todo web app
# Progress: 1/6 (16.7%)
#
# Steps:
#   ✅ step_1: Design the UI
#   ⏳ step_2: Setup project structure
#   ⏳ step_3: Implement backend API
#   ...
```

---

## 🧪 运行测试

```bash
python tests/test_all.py
```

**测试输出**：

```
=== 测试 Session Manager ===
✅ 创建会话: sess_555929a1
✅ 添加消息: 2 条
✅ 切换会话: Test 1
✅ 所有会话: 2 个

=== 测试 Long-term Memory ===
✅ 添加 3 条记忆
✅ 搜索 'Python': 1 条结果
✅ 统计: 3 条记忆, 平均重要性 0.80

=== 测试 Tool Registry ===
✅ 注册工具
✅ 执行工具: 21 * 2 = 42
✅ Schema 数量: 1

=== 测试 RSI System ===
✅ 记录经验
✅ 相关教训: 1 条
✅ Prompt 补充: 62 字符

=== 测试 Layered RSI ===
✅ 记录 memory 层经验
✅ 记录 skills 层经验
✅ 记录 tools 层经验
✅ 各层策略: 3 层

=== 测试 Planning System ===
✅ 创建计划: 58c0cb1a
✅ 开始 step_1
✅ 完成 step_1
✅ 下一步: ['step_2']

=== 测试 Feedback Loop ===
✅ 记录成功反馈
✅ 记录失败反馈
✅ 相关反馈: 1 条

=== 测试 Context Compaction ===
原始消息数: 31
压缩后消息数: 6
节省 token: 25

=== 测试 Skills Loader ===
✅ 内置技能: 3 个
✅ 匹配 'Python 函数': 1 个技能

=== 测试 MCP Connector ===
✅ 添加 MCP 服务器
✅ 工具数量: 1
✅ 执行工具成功

✅ 所有测试通过！
```

---

## 🎯 设计决策

### 为什么做这个项目？

现在市面上有很多 Agent 框架（LangChain、AutoGPT、CrewAI 等），但它们都太复杂了，新手很难理解底层原理。这个项目的目标是：**用最简单的代码，讲清楚 Agent Harness 的每一层是怎么工作的**。

### 核心设计原则

| 原则 | 说明 |
| --- | --- |
| **模块化** | 每个模块独立，可以单独学习和替换 |
| **最小依赖** | 纯 Python，无第三方依赖，新手跑起来零门槛 |
| **可插拔** | LLM 调用、工具、记忆都是可替换的 |
| **教学优先** | 代码可读性 > 性能优化 |
| **渐进式** | 从最简单的 Agent Loop 开始，一步步加功能 |

### 架构分层为什么这么分？

```
应用层 → 记忆层 → 上下文层 → 核心层 → 模型层
```

- **模型层**：最底层，只负责调用 LLM，不关心业务逻辑
- **核心层**：Agent Loop，推理循环，是整个系统的心脏
- **上下文层**：管理上下文窗口，压缩、路由、加载
- **记忆层**：短期会话 + 长期记忆 + 自改进
- **应用层**：规划、反馈、技能、工具，最贴近用户

这种分层的好处是：**每一层只做自己的事，层与层之间通过清晰的接口通信**。

---

## ✅ 验收标准

### 功能验收

| 模块 | 验收标准 | 状态 |
| --- | --- | --- |
| **Agent Loop** | 能正确调用工具并返回结果 | ✅ |
| **Session Manager** | 能创建、切换、持久化会话 | ✅ |
| **Long-term Memory** | 能添加、搜索、注入记忆 | ✅ |
| **Tool Registry** | 能注册、执行、转换工具 schema | ✅ |
| **RSI System** | 能记录经验、注入教训 | ✅ |
| **Layered RSI** | 每层独立记录经验和统计 | ✅ |
| **Context Compactor** | 能自动压缩长对话 | ✅ |
| **Skills Loader** | 能根据输入匹配技能 | ✅ |
| **MCP Connector** | 能连接外部 MCP 服务器 | ✅ |
| **Planning System** | 能创建计划、追踪进度 | ✅ |
| **Feedback Loop** | 能记录反馈、注入优化建议 | ✅ |

---

## 🚀 CI/CD 与持续开发

### 持续集成（CI）

```yaml
# .github/workflows/test.yml
name: Test
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: python tests/test_all.py
```

### 持续开发路线图

| 阶段 | 功能 | 状态 |
| --- | --- | --- |
| **v0.1** | 基础 Agent Loop + 工具系统 | ✅ 已完成 |
| **v0.2** | 会话管理 + 长期记忆 | ✅ 已完成 |
| **v0.3** | RSI 自改进 + 上下文压缩 | ✅ 已完成 |
| **v0.4** | 技能加载 + MCP 连接 | ✅ 已完成 |
| **v0.5** | Layered RSI + Planning + Feedback | ✅ 已完成 |
| **v0.6** | 向量记忆 + 工具市场 | 🔄 进行中 |
| **v1.0** | 生产级 + 完整文档 | 📋 计划中 |

---

## 🤝 如何贡献

1. Fork 这个仓库
2. 创建你的功能分支：`git checkout -b feat/my-feature`
3. 提交你的改动：`git commit -m 'feat: add my feature'`
4. 推送到分支：`git push origin feat/my-feature`
5. 提交 Pull Request

---

## 📚 参考资料

- 综述论文：[Code as Agent Harness: Toward Executable, Verifiable, and Stateful Agent Systems](https://arxiv.org/abs/2605.18747)
- Awesome 列表：[YennNing/Awesome-Code-as-Agent-Harness-Papers](https://github.com/YennNing/Awesome-Code-as-Agent-Harness-Papers)
- DeepSeek Harness：[deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness)
- OpenHands：[All-Hands-AI/OpenHands](https://github.com/All-Hands-AI/OpenHands)

---

<div align="center">

**Keep learning, keep building.** 🚀

</div>
