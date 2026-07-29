"""
群聊对话记忆管理器

双层记忆架构的「第一层」：按群维度存储完整对话流
- 包含所有用户 + 机器人回复
- 上下文连贯，AI 能感知群聊氛围
- 按群分文件：storage/conversations/group_{group_id}.json

第二层（用户画像/风格学习）保持不变，继续由 history_manager 和 style_learner 管理
"""
import json
import os
import threading
import time
from datetime import datetime
from typing import List, Dict, Optional

from joha.config.paths import CONVERSATIONS_DIR
from joha.config.cache import LRUCache
from joha.config.logger import tprint

MAX_MESSAGES = 500
CACHE_TTL = 60


class GroupConversationManager:
    def __init__(self):
        os.makedirs(CONVERSATIONS_DIR, exist_ok=True)
        self._cache: LRUCache = LRUCache(capacity=30)
        self._locks: Dict[str, threading.Lock] = {}
        self._lock_lock = threading.Lock()

    def _get_lock(self, group_id: str) -> threading.Lock:
        with self._lock_lock:
            if group_id not in self._locks:
                self._locks[group_id] = threading.Lock()
            return self._locks[group_id]

    def _path(self, group_id: str) -> str:
        safe = str(group_id).replace("/", "_").replace("\\", "_")
        return os.path.join(CONVERSATIONS_DIR, f"group_{safe}.json")

    def _load(self, group_id: str) -> List[Dict]:
        path = self._path(group_id)
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("messages", [])
        except Exception as e:
            tprint("warning", f"[群对话] 读取失败 群{group_id}: {e}")
            return []

    def _save(self, group_id: str, messages: List[Dict]):
        path = self._path(group_id)
        try:
            trimmed = messages[-MAX_MESSAGES:]
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"group_id": group_id, "messages": trimmed}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            tprint("warning", f"[群对话] 保存失败 群{group_id}: {e}")

    def add_message(self, group_id: str, user_id: str, message: str,
                    role: str = "user", message_id: Optional[str] = None):
        """
        记录一条群消息（自带去重，同 message_id 不再重复写入）
        """
        lock = self._get_lock(group_id)
        with lock:
            messages = self._load(group_id)

            if message_id:
                for m in messages:
                    if m.get("message_id") == message_id:
                        return

            messages.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "user_id": str(user_id),
                "role": role,
                "message": message,
                "message_id": message_id or "",
            })
            self._save(group_id, messages)
            self._cache.delete(f"conv_{group_id}")

    def add_user_message(self, group_id: str, user_id: str, message: str, message_id: Optional[str] = None):
        """记录用户消息"""
        self.add_message(group_id, user_id, message, role="user", message_id=message_id)

    def add_bot_reply(self, group_id: str, message: str, message_id: Optional[str] = None):
        """记录机器人回复"""
        self.add_message(group_id, "bot", message, role="assistant", message_id=message_id)

    def get_context(self, group_id: str, limit: int = 30) -> List[Dict]:
        """
        获取群聊上下文（用于构建 AI 对话历史）
        直接返回 OpenAI messages 格式
        """
        cache_key = f"conv_{group_id}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached[-limit:]

        lock = self._get_lock(group_id)
        with lock:
            messages = self._load(group_id)

        context = []
        for msg in messages[-limit:]:
            role = msg.get("role", "user")
            text = msg.get("message", "")
            uid = msg.get("user_id", "")
            if not text:
                continue
            if role == "assistant":
                context.append({"role": "assistant", "content": text})
            else:
                context.append({"role": "user", "content": f"[用户{uid}] {text}"})

        self._cache.set(cache_key, context, ttl=CACHE_TTL)
        return context

    def get_recent_messages(self, group_id: str, limit: int = 30) -> List[Dict]:
        """获取最近的原始消息列表"""
        lock = self._get_lock(group_id)
        with lock:
            messages = self._load(group_id)
        return messages[-limit:]


# 全局实例
group_conversation = GroupConversationManager()
