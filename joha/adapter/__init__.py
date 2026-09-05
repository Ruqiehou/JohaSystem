"""
Joha Adapter —— 主入口模块
NapCat 适配层：连接、事件、API、配置管理
"""

from __future__ import annotations

from joha.adapter.message_client import MessageClient
from joha.adapter.config import Config, ConfigManager, config_manager, setup_logging, get_logger
from joha.adapter.transport import NapCatClient
from joha.adapter.protocol import (
    BotAPI,
    EventBus,
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

__version__: str = "3.7.0"

__all__: list[str] = [
    "NapCatClient",
    "BotAPI",
    "EventBus",
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
    "Config",
    "ConfigManager",
    "config_manager",
    "setup_logging",
    "get_logger",
    "MessageClient",
    "__version__",
]
