"""
群聊记忆管理器

维护每个群的长期记忆摘要，包括：
- 话题摘要（最近讨论的主题）
- 长期事实（群配置、用户偏好、约定等）
- 用户关系标签

不与 group_conversation 混用，独立文件：
  storage/memory/group_{group_id}.json
"""
import json
import os
import threading
from datetime import datetime
from typing import Dict, List, Optional

from joha.config.paths import MEMORY_DIR
from joha.config.logger import tprint

MAX_FACTS = 50
CACHE_TTL = 120


class GroupMemory:
    def __init__(self, group_id: str):
        self.group_id = str(group_id)
        self._path = os.path.join(MEMORY_DIR, f"group_{self.group_id}.json")
        self._lock = threading.Lock()
        self._cache: Optional[Dict] = None

    def _default(self) -> Dict:
        return {
            "group_id": self.group_id,
            "summary": "",
            "topics": [],
            "facts": [],
            "updated_at": "",
            "version": 1,
        }

    def _load(self) -> Dict:
        if os.path.exists(self._path):
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                tprint("warning", f"[群记忆] 读取失败 群{self.group_id}: {e}")
        return self._default()

    def _save(self, data: Dict):
        try:
            data["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self._cache = data
        except Exception as e:
            tprint("warning", f"[群记忆] 保存失败 群{self.group_id}: {e}")

    def get(self) -> Dict:
        if self._cache is None:
            self._cache = self._load()
        return self._cache

    def update_summary(self, summary: str):
        """更新群聊摘要"""
        with self._lock:
            data = self.get()
            data["summary"] = summary
            self._save(data)

    def update_topics(self, topics: List[str]):
        """更新最近话题标签"""
        with self._lock:
            data = self.get()
            data["topics"] = topics[:10]
            self._save(data)

    def add_fact(self, fact: str) -> bool:
        """添加一条长期事实（去重）"""
        with self._lock:
            data = self.get()
            facts = data.get("facts", [])
            if fact in facts:
                return False
            facts.append(fact)
            if len(facts) > MAX_FACTS:
                facts = facts[-MAX_FACTS:]
            data["facts"] = facts
            self._save(data)
            return True

    def remove_fact(self, fact: str) -> bool:
        """删除一条事实"""
        with self._lock:
            data = self.get()
            facts = data.get("facts", [])
            try:
                facts.remove(fact)
                data["facts"] = facts
                self._save(data)
                return True
            except ValueError:
                return False

    def get_context_prompt(self, max_facts: int = 5) -> str:
        """生成供 LLM 上下文的记忆片段"""
        data = self.get()
        parts = []

        if data.get("topics"):
            parts.append(f"【近期群聊话题】{'、'.join(data['topics'][:5])}")

        if data.get("facts"):
            parts.append("【群内长期事实】\n" + "\n".join(
                f"- {f}" for f in data["facts"][:max_facts]
            ))

        if data.get("summary"):
            parts.append(f"【群聊摘要】\n{data['summary'][:600]}")

        return "\n\n".join(parts)

    def get_memory_block(self) -> str:
        """快速获取记忆块（供 context_messages 插入）"""
        prompt = self.get_context_prompt()
        if prompt:
            return f"\n\n📚 群聊记忆：\n{prompt}"
        return ""


class GroupMemoryManager:
    def __init__(self):
        os.makedirs(MEMORY_DIR, exist_ok=True)
        self._instances: Dict[str, GroupMemory] = {}
        self._lock = threading.Lock()

    def _get_instance(self, group_id: str) -> GroupMemory:
        with self._lock:
            if group_id not in self._instances:
                self._instances[group_id] = GroupMemory(group_id)
            return self._instances[group_id]

    def update_summary(self, group_id: str, summary: str):
        self._get_instance(group_id).update_summary(summary)

    def update_topics(self, group_id: str, topics: List[str]):
        self._get_instance(group_id).update_topics(topics)

    def add_fact(self, group_id: str, fact: str) -> bool:
        return self._get_instance(group_id).add_fact(fact)

    def remove_fact(self, group_id: str, fact: str) -> bool:
        return self._get_instance(group_id).remove_fact(fact)

    def get_context_prompt(self, group_id: str, max_facts: int = 5) -> str:
        return self._get_instance(group_id).get_context_prompt(max_facts)

    def get_memory_block(self, group_id: str) -> str:
        return self._get_instance(group_id).get_memory_block()


# 全局实例
group_memory_manager = GroupMemoryManager()
