"""
Skills System - 技能加载系统

技能是预定义的提示词包，可以在需要时加载，增强 Agent 的能力。
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Skill:
    """一个技能"""
    name: str
    description: str
    system_prompt_addition: str  # 注入到 system prompt 的内容
    trigger_keywords: list[str] = field(default_factory=list)  # 触发关键词
    tools: list[dict] = field(default_factory=list)  # 这个技能需要的工具


class SkillLoader:
    """
    技能加载器

    功能：
    - 从目录加载技能
    - 根据用户输入自动匹配技能
    - 注入技能内容到 system prompt
    """

    def __init__(self, skills_dir: str = ".diy-agent-harness/skills"):
        self.skills_dir = Path(skills_dir)
        self.skills: dict[str, Skill] = {}
        self._load_builtin_skills()

    def _load_builtin_skills(self):
        """加载内置技能"""
        # 内置技能示例：代码审查
        self.skills["code-review"] = Skill(
            name="code-review",
            description="Review code for quality, bugs, and best practices",
            system_prompt_addition="""
You are a senior code reviewer. When reviewing code:
1. Check for correctness bugs
2. Check for security issues
3. Check for performance issues
4. Check for readability and maintainability
5. Suggest specific improvements with examples
""",
            trigger_keywords=["review", "code review", "检查代码", "代码审查"],
            tools=[],
        )

        # 内置技能示例：写作助手
        self.skills["writing-assistant"] = Skill(
            name="writing-assistant",
            description="Help with writing, editing, and improving text",
            system_prompt_addition="""
You are an expert writing assistant. When helping with writing:
1. Improve clarity and conciseness
2. Fix grammar and spelling
3. Enhance tone and style
4. Structure content logically
5. Provide actionable feedback
""",
            trigger_keywords=["write", "writing", "edit", "polish", "写", "写作", "润色"],
            tools=[],
        )

        # 内置技能示例：数据分析
        self.skills["data-analysis"] = Skill(
            name="data-analysis",
            description="Analyze data, create visualizations, and extract insights",
            system_prompt_addition="""
You are a data analyst. When analyzing data:
1. First understand the data structure
2. Clean and preprocess if needed
3. Perform exploratory analysis
4. Identify trends and patterns
5. Provide actionable insights
""",
            trigger_keywords=["data", "analysis", "analyze", "数据", "分析"],
            tools=[{"name": "calculator", "description": "Evaluate expressions"}],
        )

    def load_from_dir(self, dir_path: str):
        """从目录加载技能"""
        path = Path(dir_path)
        if not path.exists():
            return

        for skill_file in path.glob("*.json"):
            try:
                data = json.loads(skill_file.read_text())
                skill = Skill(
                    name=data["name"],
                    description=data["description"],
                    system_prompt_addition=data["system_prompt_addition"],
                    trigger_keywords=data.get("trigger_keywords", []),
                    tools=data.get("tools", []),
                )
                self.skills[skill.name] = skill
            except Exception as e:
                print(f"Warning: Failed to load skill {skill_file}: {e}")

    def match_skills(self, user_input: str, limit: int = 3) -> list[Skill]:
        """根据用户输入匹配技能"""
        input_lower = user_input.lower()
        matches = []

        for skill in self.skills.values():
            # 检查触发关键词
            for keyword in skill.trigger_keywords:
                if keyword.lower() in input_lower:
                    matches.append(skill)
                    break

        return matches[:limit]

    def build_skills_prompt(self, user_input: str) -> tuple[str, list[dict]]:
        """
        构建技能相关的 prompt 补充

        Returns:
            (prompt_addition, required_tools)
        """
        matched = self.match_skills(user_input)
        if not matched:
            return "", []

        prompt_parts = ["\n\nRelevant skills activated:"]
        all_tools = []

        for skill in matched:
            prompt_parts.append(f"\n[{skill.name}]")
            prompt_parts.append(skill.system_prompt_addition.strip())
            all_tools.extend(skill.tools)

        return "\n".join(prompt_parts), all_tools

    def list_skills(self) -> list[dict]:
        """列出所有技能"""
        return [
            {
                "name": s.name,
                "description": s.description,
                "trigger_keywords": s.trigger_keywords,
            }
            for s in self.skills.values()
        ]
