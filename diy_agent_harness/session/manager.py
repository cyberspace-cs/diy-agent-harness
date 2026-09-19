"""
Session Manager - 会话系统

管理多个会话的创建、切换、持久化。
每个会话有独立的消息历史和状态。
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class Session:
    """一个会话"""
    id: str = field(default_factory=lambda: f"sess_{uuid.uuid4().hex[:8]}")
    title: str = "New Session"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    messages: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def touch(self):
        """更新最后活跃时间"""
        self.updated_at = datetime.now()

    def add_message(self, role: str, content: str, **kwargs):
        """添加一条消息"""
        msg = {"role": role, "content": content, **kwargs}
        self.messages.append(msg)
        self.touch()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "messages": self.messages,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        return cls(
            id=data["id"],
            title=data["title"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            messages=data["messages"],
            metadata=data.get("metadata", {}),
        )


class SessionManager:
    """
    会话管理器

    功能：
    - 创建新会话
    - 切换会话
    - 列出所有会话
    - 持久化到磁盘
    - 从磁盘加载
    """

    def __init__(self, storage_dir: str = ".diy-agent-harness/sessions"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.sessions: dict[str, Session] = {}
        self.current_session_id: Optional[str] = None
        self._load_all()

    def _load_all(self):
        """从磁盘加载所有会话"""
        for path in self.storage_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text())
                session = Session.from_dict(data)
                self.sessions[session.id] = session
            except Exception as e:
                print(f"Warning: Failed to load {path}: {e}")

    def _save_session(self, session: Session):
        """保存单个会话到磁盘"""
        path = self.storage_dir / f"{session.id}.json"
        path.write_text(json.dumps(session.to_dict(), indent=2, ensure_ascii=False))

    def create_session(self, title: Optional[str] = None) -> Session:
        """创建新会话"""
        session = Session()
        if title:
            session.title = title
        self.sessions[session.id] = session
        self.current_session_id = session.id
        self._save_session(session)
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """获取指定会话"""
        return self.sessions.get(session_id)

    def switch_session(self, session_id: str) -> bool:
        """切换到指定会话"""
        if session_id in self.sessions:
            self.current_session_id = session_id
            return True
        return False

    def get_current_session(self) -> Optional[Session]:
        """获取当前会话"""
        if self.current_session_id:
            return self.sessions.get(self.current_session_id)
        return None

    def list_sessions(self) -> list[dict]:
        """列出所有会话（摘要）"""
        sessions = sorted(
            self.sessions.values(),
            key=lambda s: s.updated_at,
            reverse=True,
        )
        return [
            {
                "id": s.id,
                "title": s.title,
                "message_count": len(s.messages),
                "updated_at": s.updated_at.isoformat(),
                "is_current": s.id == self.current_session_id,
            }
            for s in sessions
        ]

    def add_message_to_current(self, role: str, content: str, **kwargs) -> Optional[Session]:
        """向当前会话添加消息"""
        session = self.get_current_session()
        if session:
            session.add_message(role, content, **kwargs)
            self._save_session(session)
        return session

    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            path = self.storage_dir / f"{session_id}.json"
            if path.exists():
                path.unlink()
            if self.current_session_id == session_id:
                self.current_session_id = None
            return True
        return False

    def rename_session(self, session_id: str, new_title: str) -> bool:
        """重命名会话"""
        session = self.sessions.get(session_id)
        if session:
            session.title = new_title
            self._save_session(session)
            return True
        return False
