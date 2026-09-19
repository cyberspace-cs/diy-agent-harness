"""
Memory System - 记忆系统

两层记忆：
- Working Memory：当前会话的工作记忆（短期）
- Long-term Memory：跨会话的长期记忆（向量存储 / KV 存储）
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class MemoryItem:
    """一条长期记忆"""
    id: str = field(default_factory=lambda: f"mem_{uuid.uuid4().hex[:8]}")
    content: str = ""
    category: str = "general"  # user_preference / fact / lesson / conversation
    importance: float = 0.5  # 0.0 - 1.0
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "category": self.category,
            "importance": self.importance,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryItem":
        return cls(
            id=data["id"],
            content=data["content"],
            category=data["category"],
            importance=data["importance"],
            created_at=datetime.fromisoformat(data["created_at"]),
            metadata=data.get("metadata", {}),
        )


class LongTermMemory:
    """
    长期记忆存储

    功能：
    - 添加记忆
    - 按类别搜索
    - 按重要性排序
    - 持久化到磁盘
    """

    def __init__(self, storage_dir: str = ".diy-agent-harness/memory"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.memories: dict[str, MemoryItem] = {}
        self._load_all()

    def _load_all(self):
        """从磁盘加载所有记忆"""
        path = self.storage_dir / "memories.json"
        if path.exists():
            try:
                data = json.loads(path.read_text())
                for item_data in data:
                    item = MemoryItem.from_dict(item_data)
                    self.memories[item.id] = item
            except Exception as e:
                print(f"Warning: Failed to load memories: {e}")

    def _save_all(self):
        """保存所有记忆到磁盘"""
        path = self.storage_dir / "memories.json"
        data = [item.to_dict() for item in self.memories.values()]
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    def add(self, content: str, category: str = "general",
            importance: float = 0.5, metadata: Optional[dict] = None) -> MemoryItem:
        """添加一条记忆"""
        item = MemoryItem(
            content=content,
            category=category,
            importance=importance,
            metadata=metadata or {},
        )
        self.memories[item.id] = item
        self._save_all()
        return item

    def search(self, query: Optional[str] = None,
               category: Optional[str] = None,
               min_importance: float = 0.0,
               limit: int = 10) -> list[MemoryItem]:
        """
        搜索记忆

        简单实现：按类别和重要性过滤，按时间倒序返回。
        生产环境可以换成向量搜索。
        """
        results = list(self.memories.values())

        # 按类别过滤
        if category:
            results = [m for m in results if m.category == category]

        # 按重要性过滤
        results = [m for m in results if m.importance >= min_importance]

        # 简单的关键词匹配（生产环境用向量搜索）
        if query:
            query_lower = query.lower()
            results = [m for m in results if query_lower in m.content.lower()]

        # 按重要性和时间排序
        results.sort(key=lambda m: (m.importance, m.created_at), reverse=True)

        return results[:limit]

    def get_relevant_for_prompt(self, query: str, limit: int = 5) -> str:
        """
        获取相关记忆，格式化为可以注入到 system prompt 的文本
        """
        items = self.search(query=query, limit=limit)
        if not items:
            return ""

        lines = ["Relevant memories:"]
        for item in items:
            lines.append(f"- [{item.category}] {item.content}")
        return "\n".join(lines)

    def delete(self, memory_id: str) -> bool:
        """删除一条记忆"""
        if memory_id in self.memories:
            del self.memories[memory_id]
            self._save_all()
            return True
        return False

    def get_stats(self) -> dict:
        """获取记忆统计"""
        categories: dict[str, int] = {}
        for m in self.memories.values():
            categories[m.category] = categories.get(m.category, 0) + 1

        return {
            "total": len(self.memories),
            "by_category": categories,
            "avg_importance": (
                sum(m.importance for m in self.memories.values()) / len(self.memories)
                if self.memories else 0
            ),
        }
