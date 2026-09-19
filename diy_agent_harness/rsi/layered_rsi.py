"""
Layered RSI - 分层递归自改进

让 Harness 的每一层都能从经验中学习和改进：
- Memory RSI：优化记忆检索策略
- Context RSI：优化上下文压缩策略
- Skills RSI：优化技能触发匹配
- Tools RSI：优化工具选择策略
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class LayerExperience:
    """一层的经验记录"""
    layer: str  # memory / context / skills / tools
    operation: str  # 执行的操作
    input_data: dict = field(default_factory=dict)
    output_data: dict = field(default_factory=dict)
    success: bool = True
    feedback_score: float = 0.5  # 0.0 - 1.0
    notes: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "layer": self.layer,
            "operation": self.operation,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "success": self.success,
            "feedback_score": self.feedback_score,
            "notes": self.notes,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LayerExperience":
        return cls(
            layer=data["layer"],
            operation=data["operation"],
            input_data=data.get("input_data", {}),
            output_data=data.get("output_data", {}),
            success=data.get("success", True),
            feedback_score=data.get("feedback_score", 0.5),
            notes=data.get("notes", ""),
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )


class LayeredRSI:
    """
    分层 RSI 系统

    每一层都有自己的：
    - 经验记录
    - 策略优化
    - 自适应调整
    """

    def __init__(self, storage_dir: str = ".diy-agent-harness/layered_rsi"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.experiences: dict[str, list[LayerExperience]] = {}
        self.layer_stats: dict[str, dict] = {}
        self._load_all()

    def _load_all(self):
        """从磁盘加载"""
        path = self.storage_dir / "experiences.json"
        if path.exists():
            try:
                data = json.loads(path.read_text())
                for layer_data in data:
                    layer = layer_data.get("layer", "unknown")
                    if layer not in self.experiences:
                        self.experiences[layer] = []
                    self.experiences[layer].append(LayerExperience.from_dict(layer_data))
            except Exception as e:
                print(f"Warning: Failed to load experiences: {e}")

    def _save_all(self):
        """保存到磁盘"""
        path = self.storage_dir / "experiences.json"
        all_data = []
        for layer, exps in self.experiences.items():
            all_data.extend([e.to_dict() for e in exps])
        path.write_text(json.dumps(all_data, indent=2, ensure_ascii=False))

    def record_experience(
        self,
        layer: str,
        operation: str,
        input_data: dict,
        output_data: dict,
        success: bool = True,
        feedback_score: float = 0.5,
        notes: str = "",
    ):
        """记录一层的经验"""
        exp = LayerExperience(
            layer=layer,
            operation=operation,
            input_data=input_data,
            output_data=output_data,
            success=success,
            feedback_score=feedback_score,
            notes=notes,
        )
        if layer not in self.experiences:
            self.experiences[layer] = []
        self.experiences[layer].append(exp)

        # 更新统计
        self._update_layer_stats(layer)

        self._save_all()

    def _update_layer_stats(self, layer: str):
        """更新一层的统计"""
        exps = self.experiences.get(layer, [])
        if not exps:
            return

        successful = sum(1 for e in exps if e.success)
        avg_score = sum(e.feedback_score for e in exps) / len(exps)

        self.layer_stats[layer] = {
            "total": len(exps),
            "success_rate": successful / len(exps),
            "avg_feedback_score": avg_score,
        }

    def get_layer_strategy(self, layer: str) -> dict:
        """
        获取一层的优化策略

        根据历史经验，返回这一层的优化建议。
        """
        stats = self.layer_stats.get(layer, {})
        exps = self.experiences.get(layer, [])

        strategy = {
            "layer": layer,
            "total_experiences": stats.get("total", 0),
            "success_rate": stats.get("success_rate", 0.5),
            "avg_feedback_score": stats.get("avg_feedback_score", 0.5),
            "recommendations": [],
        }

        # 基于统计生成建议
        if stats.get("success_rate", 0.5) < 0.5:
            strategy["recommendations"].append(
                "Success rate is low - review recent failures and adjust strategy."
            )

        if stats.get("avg_feedback_score", 0.5) < 0.5:
            strategy["recommendations"].append(
                "Feedback scores are low - consider alternative approaches."
            )

        # 找最近失败的操作
        recent_failures = [
            e for e in exps[-10:] if not e.success
        ]
        if recent_failures:
            failed_ops = list(set(e.operation for e in recent_failures))
            strategy["recommendations"].append(
                f"Recently failing operations: {', '.join(failed_ops)}"
            )

        return strategy

    def get_all_strategies(self) -> dict:
        """获取所有层的优化策略"""
        return {
            layer: self.get_layer_strategy(layer)
            for layer in self.experiences.keys()
        }

    def get_summary_report(self) -> str:
        """生成所有层的总结报告"""
        lines = ["# Layered RSI Report", ""]

        for layer in ["memory", "context", "skills", "tools"]:
            stats = self.layer_stats.get(layer, {})
            if not stats:
                continue

            lines.append(f"## {layer.upper()}")
            lines.append(f"- Total experiences: {stats.get('total', 0)}")
            lines.append(f"- Success rate: {stats.get('success_rate', 0):.1%}")
            lines.append(f"- Avg feedback score: {stats.get('avg_feedback_score', 0):.2f}")
            lines.append("")

        return "\n".join(lines)
