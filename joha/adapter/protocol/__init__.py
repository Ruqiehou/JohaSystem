"""
协议层 (Protocol Layer)
提供 OneBot 协议解析、事件模型、API 封装与事件分发能力
"""

from __future__ import annotations

from .api import BotAPI
from .emoji_map import FACE_NAMES, get_face_name
from .event_bus import EventBus
from .event_dispatcher import EventDispatcher, PriorityEventDispatcher
from .events import (
    BaseEvent,
    FriendRecallNotice,
    FriendRequestEvent,
    GroupBanNotice,
    GroupDecreaseNotice,
    GroupIncreaseNotice,
    GroupMessageEvent,
    GroupRecallNotice,
    GroupRequestEvent,
    Message,
    NoticeEvent,
    PokeNotice,
    PrivateMessageEvent,
    RequestEvent,
)
from .interfaces import IBotAPI, IEventDispatcher
from .message_segment import MessageSegment

__all__: list[str] = [
    "BotAPI",
    "MessageSegment",
    "EventBus",
    "EventDispatcher",
    "PriorityEventDispatcher",
    "IBotAPI",
    "IEventDispatcher",
    "BaseEvent",
    "Message",
    "GroupMessageEvent",
    "PrivateMessageEvent",
    "NoticeEvent",
    "GroupIncreaseNotice",
    "GroupDecreaseNotice",
    "GroupBanNotice",
    "GroupRecallNotice",
    "FriendRecallNotice",
    "PokeNotice",
    "RequestEvent",
    "FriendRequestEvent",
    "GroupRequestEvent",
    "FACE_NAMES",
    "get_face_name",
]
