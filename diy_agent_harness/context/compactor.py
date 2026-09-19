"""
Context Compaction - 上下文压缩

当对话历史太长时，自动压缩旧消息，保留关键信息，避免上下文窗口爆炸。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CompactionResult:
    """压缩结果"""
    original_messages: int = 0
    compacted_messages: int = 0
    summary: str = ""
    tokens_saved: int = 0


class ContextCompactor:
    """
    上下文压缩器

    策略：
    1. 保留系统消息（第一条）
    2. 保留最近 N 条消息
    3. 中间的旧消息压缩成摘要
    """

    def __init__(
        self,
        max_messages: int = 20,
        keep_recent: int = 6,
        summarize_old: bool = True,
    ):
        self.max_messages = max_messages
        self.keep_recent = keep_recent
        self.summarize_old = summarize_old

    def should_compact(self, messages: list[dict]) -> bool:
        """判断是否需要压缩"""
        return len(messages) > self.max_messages

    def compact(self, messages: list[dict]) -> tuple[list[dict], CompactionResult]:
        """
        压缩消息历史

        策略：
        1. 保留第一条 system 消息
        2. 保留最近 keep_recent 条消息
        3. 中间的旧消息压缩成一条 summary 消息
        """
        if not self.should_compact(messages):
            return messages, CompactionResult(
                original_messages=len(messages),
                compacted_messages=len(messages),
                summary="",
                tokens_saved=0,
            )

        # 分离 system 消息和其他消息
        system_messages = [m for m in messages if m.get("role") == "system"]
        other_messages = [m for m in messages if m.get("role") != "system"]

        # 保留最近的消息
        recent_messages = other_messages[-self.keep_recent:]
        old_messages = other_messages[:-self.keep_recent]

        if not old_messages:
            return messages, CompactionResult(
                original_messages=len(messages),
                compacted_messages=len(messages),
                summary="",
                tokens_saved=0,
            )

        # 压缩旧消息
        summary = self._summarize(old_messages)

        # 构建压缩后的消息列表
        compacted = system_messages + [
            {"role": "system", "content": f"[Summary of earlier conversation]: {summary}"}
        ] + recent_messages

        return compacted, CompactionResult(
            original_messages=len(messages),
            compacted_messages=len(compacted),
            summary=summary,
            tokens_saved=len(messages) - len(compacted),
        )

    def _summarize(self, messages: list[dict]) -> str:
        """
        简单的摘要生成

        生产环境可以用 LLM 来做更好的摘要。
        这里用简单的提取方式：提取关键信息。
        """
        user_messages = [m for m in messages if m.get("role") == "user"]
        assistant_messages = [m for m in messages if m.get("role") == "assistant"]

        parts = []

        if user_messages:
            parts.append(f"{len(user_messages)} user messages")
            # 提取最后一条用户消息的要点
            last_user = user_messages[-1].get("content", "")[:100]
            if last_user:
                parts.append(f"last user asked: '{last_user}...'")

        if assistant_messages:
            parts.append(f"{len(assistant_messages)} assistant responses")

        return "; ".join(parts) if parts else "earlier conversation"
