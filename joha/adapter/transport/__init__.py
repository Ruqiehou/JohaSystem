"""
传输层 (Transport Layer)
提供 WebSocket 连接管理与原始消息收发能力
"""

from __future__ import annotations

from .client import NapCatClient
from .interfaces import (
    APIResponse,
    EventHandler,
    IClient,
    IConnectionEventListener,
    MessageSegmentType,
)

__all__: list[str] = [
    "NapCatClient",
    "IClient",
    "IConnectionEventListener",
    "APIResponse",
    "EventHandler",
    "MessageSegmentType",
]
