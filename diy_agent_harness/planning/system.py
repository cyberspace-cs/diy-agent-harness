"""
Planning System - 规划系统

让 Agent 先规划再行动，而不是直接走一步看一步。
参考 Code as Agent Harness 综述的 Planning for Code Agents 部分。
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class StepStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PlanStep:
    """计划的一步"""
    step_id: str
    description: str
    status: StepStatus = StepStatus.PENDING
    depends_on: list[str] = field(default_factory=list)
    result: Optional[str] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "step_id": self.step_id,
            "description": self.description,
            "status": self.status.value,
            "depends_on": self.depends_on,
            "result": self.result,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PlanStep":
        return cls(
            step_id=data["step_id"],
            description=data["description"],
            status=StepStatus(data.get("status", "pending")),
            depends_on=data.get("depends_on", []),
            result=data.get("result"),
            error=data.get("error"),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
        )


@dataclass
class Plan:
    """完整的计划"""
    plan_id: str
    task: str
    steps: list[PlanStep] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    status: StepStatus = StepStatus.PENDING

    def to_dict(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "task": self.task,
            "steps": [s.to_dict() for s in self.steps],
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Plan":
        return cls(
            plan_id=data["plan_id"],
            task=data["task"],
            steps=[PlanStep.from_dict(s) for s in data.get("steps", [])],
            created_at=datetime.fromisoformat(data["created_at"]),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            status=StepStatus(data.get("status", "pending")),
        )

    def get_pending_steps(self) -> list[PlanStep]:
        """获取可以执行的步骤（依赖都完成了）"""
        completed_ids = {s.step_id for s in self.steps if s.status == StepStatus.COMPLETED}
        pending = []
        for step in self.steps:
            if step.status == StepStatus.PENDING:
                if all(dep in completed_ids for dep in step.depends_on):
                    pending.append(step)
        return pending

    def get_progress(self) -> dict:
        """获取进度"""
        total = len(self.steps)
        completed = sum(1 for s in self.steps if s.status == StepStatus.COMPLETED)
        failed = sum(1 for s in self.steps if s.status == StepStatus.FAILED)
        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "progress_pct": (completed / total * 100) if total > 0 else 0,
        }


class PlanningSystem:
    """
    规划系统

    让 Agent 先做计划，再逐步执行。
    支持：
    - 步骤依赖
    - 进度追踪
    - 失败重试
    - 计划持久化
    """

    def __init__(self, storage_dir: str = ".diy-agent-harness/plans"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.current_plan: Optional[Plan] = None
        self.plans: dict[str, Plan] = {}
        self._load_all()

    def _load_all(self):
        """从磁盘加载所有计划"""
        for file in self.storage_dir.glob("plan_*.json"):
            try:
                data = json.loads(file.read_text())
                plan = Plan.from_dict(data)
                self.plans[plan.plan_id] = plan
            except Exception as e:
                print(f"Warning: Failed to load plan {file}: {e}")

    def _save_plan(self, plan: Plan):
        """保存计划到磁盘"""
        path = self.storage_dir / f"plan_{plan.plan_id}.json"
        path.write_text(json.dumps(plan.to_dict(), indent=2, ensure_ascii=False))

    def create_plan(self, task: str, step_descriptions: list[str]) -> Plan:
        """
        创建新计划

        Args:
            task: 任务描述
            step_descriptions: 步骤描述列表

        Returns:
            新创建的 Plan
        """
        import uuid
        plan_id = uuid.uuid4().hex[:8]

        steps = []
        for i, desc in enumerate(step_descriptions):
            step = PlanStep(
                step_id=f"step_{i+1}",
                description=desc,
                depends_on=[f"step_{i}"] if i > 0 else [],  # 默认串行依赖
            )
            steps.append(step)

        plan = Plan(
            plan_id=plan_id,
            task=task,
            steps=steps,
            status=StepStatus.IN_PROGRESS,
        )

        self.plans[plan_id] = plan
        self.current_plan = plan
        self._save_plan(plan)

        return plan

    def start_step(self, step_id: str) -> Optional[PlanStep]:
        """开始执行某一步"""
        if not self.current_plan:
            return None

        for step in self.current_plan.steps:
            if step.step_id == step_id:
                step.status = StepStatus.IN_PROGRESS
                step.started_at = datetime.now()
                self._save_plan(self.current_plan)
                return step

        return None

    def complete_step(self, step_id: str, result: str) -> Optional[PlanStep]:
        """完成某一步"""
        if not self.current_plan:
            return None

        for step in self.current_plan.steps:
            if step.step_id == step_id:
                step.status = StepStatus.COMPLETED
                step.result = result
                step.completed_at = datetime.now()
                self._save_plan(self.current_plan)
                self._check_plan_completion()
                return step

        return None

    def fail_step(self, step_id: str, error: str) -> Optional[PlanStep]:
        """标记某一步失败"""
        if not self.current_plan:
            return None

        for step in self.current_plan.steps:
            if step.step_id == step_id:
                step.status = StepStatus.FAILED
                step.error = error
                step.completed_at = datetime.now()
                self._save_plan(self.current_plan)
                self._check_plan_completion()
                return step

        return None

    def _check_plan_completion(self):
        """检查计划是否完成"""
        if not self.current_plan:
            return

        all_done = all(
            s.status in (StepStatus.COMPLETED, StepStatus.FAILED, StepStatus.SKIPPED)
            for s in self.current_plan.steps
        )

        if all_done:
            self.current_plan.status = StepStatus.COMPLETED
            self.current_plan.completed_at = datetime.now()
            self._save_plan(self.current_plan)

    def get_next_steps(self) -> list[PlanStep]:
        """获取下一步要执行的步骤"""
        if not self.current_plan:
            return []
        return self.current_plan.get_pending_steps()

    def get_plan_summary(self) -> str:
        """获取计划总结"""
        if not self.current_plan:
            return "No active plan"

        progress = self.current_plan.get_progress()
        lines = [
            f"Plan: {self.current_plan.task}",
            f"Progress: {progress['completed']}/{progress['total']} ({progress['progress_pct']:.1f}%)",
            "",
            "Steps:",
        ]

        for step in self.current_plan.steps:
            status_icon = {
                StepStatus.PENDING: "⏳",
                StepStatus.IN_PROGRESS: "🔄",
                StepStatus.COMPLETED: "✅",
                StepStatus.FAILED: "❌",
                StepStatus.SKIPPED: "⏭️",
            }[step.status]
            lines.append(f"  {status_icon} {step.step_id}: {step.description}")

        return "\n".join(lines)

    def switch_plan(self, plan_id: str) -> bool:
        """切换到另一个计划"""
        if plan_id in self.plans:
            self.current_plan = self.plans[plan_id]
            return True
        return False

    def list_plans(self) -> list[dict]:
        """列出所有计划"""
        return [
            {
                "plan_id": p.plan_id,
                "task": p.task,
                "status": p.status.value,
                "created_at": p.created_at.isoformat(),
            }
            for p in self.plans.values()
        ]
