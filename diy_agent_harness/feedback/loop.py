"""
Feedback Loop - 反馈循环

从执行结果中学习，不断改进。
参考 Code as Agent Harness 综述的 Feedback-Guided Iterative Debugging 部分。
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class FeedbackType(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    WARNING = "warning"
    SUGGESTION = "suggestion"


@dataclass
class Feedback:
    """一条反馈"""
    feedback_id: str
    feedback_type: FeedbackType
    context: str  # 发生了什么
    insight: str  # 我们学到了什么
    action: str  # 下次怎么做
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "feedback_id": self.feedback_id,
            "feedback_type": self.feedback_type.value,
            "context": self.context,
            "insight": self.insight,
            "action": self.action,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Feedback":
        return cls(
            feedback_id=data["feedback_id"],
            feedback_type=FeedbackType(data["feedback_type"]),
            context=data["context"],
            insight=data["insight"],
            action=data["action"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )


class FeedbackLoop:
    """
    反馈循环系统

    从每次执行中学习：
    - 成功了，总结经验
    - 失败了，分析原因，下次避免
    - 把学到的东西注入到下次的执行中
    """

    def __init__(self, storage_dir: str = ".diy-agent-harness/feedback"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.feedbacks: list[Feedback] = []
        self._load_all()

    def _load_all(self):
        """从磁盘加载所有反馈"""
        path = self.storage_dir / "feedbacks.json"
        if path.exists():
            try:
                data = json.loads(path.read_text())
                self.feedbacks = [Feedback.from_dict(f) for f in data]
            except Exception as e:
                print(f"Warning: Failed to load feedbacks: {e}")

    def _save_all(self):
        """保存到磁盘"""
        path = self.storage_dir / "feedbacks.json"
        path.write_text(json.dumps([f.to_dict() for f in self.feedbacks], indent=2, ensure_ascii=False))

    def record_success(self, context: str, insight: str, action: str = ""):
        """记录成功反馈"""
        import uuid
        fb = Feedback(
            feedback_id=uuid.uuid4().hex[:8],
            feedback_type=FeedbackType.SUCCESS,
            context=context,
            insight=insight,
            action=action or "Keep doing what works.",
        )
        self.feedbacks.append(fb)
        self._save_all()

    def record_failure(self, context: str, insight: str, action: str = ""):
        """记录失败反馈"""
        import uuid
        fb = Feedback(
            feedback_id=uuid.uuid4().hex[:8],
            feedback_type=FeedbackType.FAILURE,
            context=context,
            insight=insight,
            action=action or "Avoid this approach next time.",
        )
        self.feedbacks.append(fb)
        self._save_all()

    def record_warning(self, context: str, insight: str, action: str = ""):
        """记录警告反馈"""
        import uuid
        fb = Feedback(
            feedback_id=uuid.uuid4().hex[:8],
            feedback_type=FeedbackType.WARNING,
            context=context,
            insight=insight,
            action=action,
        )
        self.feedbacks.append(fb)
        self._save_all()

    def get_relevant_feedback(self, query: str, limit: int = 5) -> list[Feedback]:
        """获取相关的反馈（简单关键词匹配）"""
        query_lower = query.lower()
        relevant = []
        for fb in self.feedbacks[-50:]:  # 只看最近 50 条
            if query_lower in fb.context.lower() or query_lower in fb.insight.lower():
                relevant.append(fb)
        return relevant[-limit:]

    def build_prompt_addition(self, task: str) -> str:
        """
        构建注入到 system prompt 的补充内容

        基于相关反馈，告诉 Agent 之前学到的经验。
        """
        relevant = self.get_relevant_feedback(task, limit=3)
        if not relevant:
            return ""

        lines = [
            "",
            "Lessons learned from previous experiences:",
        ]

        for fb in relevant:
            icon = {
                FeedbackType.SUCCESS: "✅",
                FeedbackType.FAILURE: "❌",
                FeedbackType.WARNING: "⚠️",
            }[fb.feedback_type]
            lines.append(f"{icon} {fb.insight}")
            if fb.action:
                lines.append(f"   Action: {fb.action}")

        return "\n".join(lines)

    def get_stats(self) -> dict:
        """获取统计"""
        total = len(self.feedbacks)
        success = sum(1 for f in self.feedbacks if f.feedback_type == FeedbackType.SUCCESS)
        failure = sum(1 for f in self.feedbacks if f.feedback_type == FeedbackType.FAILURE)
        warning = sum(1 for f in self.feedbacks if f.feedback_type == FeedbackType.WARNING)

        return {
            "total": total,
            "success": success,
            "failure": failure,
            "warning": warning,
            "success_rate": (success / total * 100) if total > 0 else 0,
        }

    def get_summary_report(self) -> str:
        """生成总结报告"""
        stats = self.get_stats()
        lines = [
            "# Feedback Loop Report",
            "",
            f"Total feedbacks: {stats['total']}",
            f"Success: {stats['success']}",
            f"Failure: {stats['failure']}",
            f"Warning: {stats['warning']}",
            f"Success rate: {stats['success_rate']:.1f}%",
        ]
        return "\n".join(lines)
