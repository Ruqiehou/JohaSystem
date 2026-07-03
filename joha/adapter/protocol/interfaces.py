"""
协议层接口定义
提供 BotAPI Protocol 与事件分发器抽象基类
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import (
    Any, Awaitable, Callable, Dict, List, Optional, Union, TypeAlias, Type,
)
from typing import Protocol

from joha.adapter.transport.interfaces import MessageSegmentType

logger = logging.getLogger(__name__)

# ---- 基础类型别名 ----
APIResponse: TypeAlias = Dict[str, Any]


# ==================== 事件分发器接口 ====================

class IEventDispatcher(ABC):
    """事件分发器抽象基类 —— 负责事件的注册、管理与分发"""

    def __init__(self) -> None:
        self._handlers: Dict[str, List[Dict[str, Any]]] = {
            "group": [],
            "private": [],
            "notice": [],
            "request": [],
        }
        self._event_types: Dict[str, Any] = {}

    @abstractmethod
    def register_handler(
        self,
        event_type: str,
        handler: Callable[..., Any],
        priority: int = 0,
        name: Optional[str] = None,
    ) -> None:
        ...

    @abstractmethod
    def unregister_handler(self, event_type: str, handler: Callable[..., Any]) -> bool:
        ...

    @abstractmethod
    async def dispatch(self, event_type: str, data: Dict[str, Any]) -> None:
        ...

    @abstractmethod
    def get_handler_count(self, event_type: Optional[str] = None) -> int:
        ...


# ==================== API 接口 ====================

class IBotAPI(Protocol):
    """BotAPI Protocol —— 插件只依赖此接口，不依赖具体 BotAPI 类"""

    async def call(self, action: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        ...

    async def send_group_message(
        self,
        group_id: int,
        message: str = "",
        image_path: Optional[str] = None,
        at_user_id: Optional[int] = None,
        reply_message_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        ...

    async def send_private_message(
        self,
        user_id: int,
        message: str = "",
        image_path: Optional[str] = None,
        reply_message_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        ...

    async def send_group_message_segments(
        self,
        group_id: int,
        segments: List[MessageSegmentType],
        reply_message_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        ...

    async def send_private_message_segments(
        self,
        user_id: int,
        segments: List[MessageSegmentType],
        reply_message_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        ...

    async def delete_message(self, message_id: int) -> Dict[str, Any]:
        ...

    async def get_message(self, message_id: int) -> Dict[str, Any]:
        ...

    async def group_poke(self, group_id: int, user_id: int) -> Dict[str, Any]:
        ...

    async def friend_poke(self, user_id: int) -> Dict[str, Any]:
        ...

    async def get_group_list(self) -> Dict[str, Any]:
        ...

    async def get_group_member_list(self, group_id: int) -> Dict[str, Any]:
        ...

    async def get_group_member_info(self, group_id: int, user_id: int) -> Dict[str, Any]:
        ...

    async def set_group_ban(self, group_id: int, user_id: int, duration: int = 1800) -> Dict[str, Any]:
        ...

    async def set_group_kick(self, group_id: int, user_id: int, reject_add_request: bool = False) -> Dict[str, Any]:
        ...

    async def set_group_card(self, group_id: int, user_id: int, card: str = "") -> Dict[str, Any]:
        ...

    async def get_friend_list(self) -> Dict[str, Any]:
        ...

    async def get_login_info(self) -> Dict[str, Any]:
        ...

    async def get_stranger_info(self, user_id: int) -> Dict[str, Any]:
        ...

    async def set_friend_add_request(self, flag: str, approve: bool = True, remark: str = "") -> Dict[str, Any]:
        ...

    async def set_group_add_request(self, flag: str, sub_type: str, approve: bool = True, reason: str = "") -> Dict[str, Any]:
        ...

    async def send_like(self, user_id: int, times: int = 1) -> Dict[str, Any]:
        ...

    async def get_version_info(self) -> Dict[str, Any]:
        ...
