"""
兼容导出层 (Core Facade)
统一 re-export transport + protocol 的所有公开类，
使 joha.adapter.core.xxx 的导入路径继续工作
"""

from __future__ import annotations

# ---- transport 层 ----
from joha.adapter.transport import NapCatClient
from joha.adapter.transport.interfaces import (
    IClient,
    IConnectionEventListener,
)

# ---- protocol 层 ----
from joha.adapter.protocol import (
    BotAPI,
    EventBus,
    EventDispatcher,
    PriorityEventDispatcher,
    IBotAPI,
    IEventDispatcher,
    MessageSegment,
    BaseEvent,
    Message,
    GroupMessageEvent,
    PrivateMessageEvent,
    NoticeEvent,
    GroupIncreaseNotice,
    GroupDecreaseNotice,
    GroupBanNotice,
    GroupRecallNotice,
    FriendRecallNotice,
    PokeNotice,
    RequestEvent,
    FriendRequestEvent,
    GroupRequestEvent,
    FACE_NAMES,
    get_face_name,
)

__all__: list[str] = [
    # transport
    "NapCatClient",
    "IClient",
    "IConnectionEventListener",
    # protocol
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
