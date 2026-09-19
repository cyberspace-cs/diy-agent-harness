"""
RSI (Recursive Self-Improvement) System - 递归自改进系统

让 Agent 从自己的经验中学习，不断改进自己的行为。
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class Experience:
    """一条经验记录"""
    id: str = field(default_factory=lambda: f"exp_{uuid.uuid4().hex[:8]}")
    task: str = ""  # 任务描述
    context: str = ""  # 上下文
    action: str = ""  # 采取的行动
    outcome: str = ""  # 结果
    success: bool = False  # 是否成功
    lesson: str = ""  # 学到的教训
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "task": self.task,
            "context": self.context,
            "action": self.action,
            "outcome": self.outcome,
            "success": self.success,
            "lesson": self.lesson,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Experience":
        return cls(
            id=data["id"],
            task=data["task"],
            context=data["context"],
            action=data["action"],
            outcome=data["outcome"],
            success=data["success"],
            lesson=data["lesson"],
            created_at=datetime.fromisoformat(data["created_at"]),
        )


class RSISystem:
    """
    递归自改进系统

    核心思路：
    1. 记录每次任务执行的经验
    2. 从成功和失败中提炼教训
    3. 把相关经验注入到 system prompt 中
    4. 让 Agent 在下次执行类似任务时做得更好
    """

    def __init__(self, storage_dir: str = ".diy-agent-harness/rsi"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.experiences: dict[str, Experience] = {}
        self.lessons: list[str] = []
        self._load_all()

    def _load_all(self):
        """从磁盘加载"""
        # 加载经验
        exp_path = self.storage_dir / "experiences.json"
        if exp_path.exists():
            try:
                data = json.loads(exp_path.read_text())
                for item_data in data:
                    exp = Experience.from_dict(item_data)
                    self.experiences[exp.id] = exp
            except Exception as e:
                print(f"Warning: Failed to load experiences: {e}")

        # 加载教训
        lessons_path = self.storage_dir / "lessons.json"
        if lessons_path.exists():
            try:
                self.lessons = json.loads(lessons_path.read_text())
            except Exception as e:
                print(f"Warning: Failed to load lessons: {e}")

    def _save_all(self):
        """保存到磁盘"""
        exp_path = self.storage_dir / "experiences.json"
        exp_path.write_text(json.dumps(
            [e.to_dict() for e in self.experiences.values()],
            indent=2,
            ensure_ascii=False,
        ))

        lessons_path = self.storage_dir / "lessons.json"
        lessons_path.write_text(json.dumps(self.lessons, indent=2, ensure_ascii=False))

    def record_experience(self, task: str, context: str, action: str,
                          outcome: str, success: bool, lesson: str = "") -> Experience:
        """记录一次经验"""
        exp = Experience(
            task=task,
            context=context,
            action=action,
            outcome=outcome,
            success=success,
            lesson=lesson,
        )
        self.experiences[exp.id] = exp

        # 如果有教训，加入教训库
        if lesson:
            self.lessons.append(lesson)

        self._save_all()
        return exp

    def get_relevant_lessons(self, task: str, limit: int = 5) -> list[str]:
        """获取与当前任务相关的教训"""
        # 简单实现：关键词匹配
        task_lower = task.lower()
        relevant = []

        for lesson in reversed(self.lessons):  # 最新的在前
            if any(word in lesson.lower() for word in task_lower.split()):
                relevant.append(lesson)
                if len(relevant) >= limit:
                    break

        # 如果没找到相关的，返回最新的几条
        if not relevant and self.lessons:
            relevant = self.lessons[-limit:]

        return relevant

    def build_system_prompt_addition(self, task: str) -> str:
        """
        构建 system prompt 的补充内容
        把相关教训注入进去
        """
        lessons = self.get_relevant_lessons(task)
        if not lessons:
            return ""

        lines = ["\n\nLessons learned from previous experiences:"]
        for i, lesson in enumerate(lessons, 1):
            lines.append(f"{i}. {lesson}")
        return "\n".join(lines)

    def get_stats(self) -> dict:
        """获取 RSI 统计"""
        total = len(self.experiences)
        successful = sum(1 for e in self.experiences.values() if e.success)

        return {
            "total_experiences": total,
            "success_rate": successful / total if total > 0 else 0,
            "total_lessons": len(self.lessons),
        }
