"""
传输层接口定义
定义 WebSocket 客户端与连接事件监听器的抽象接口
"""

from __future__ import annotations

import logging
from typing import (
    Any, Awaitable, Callable, Dict, Optional, TypeAlias,
)
from typing import Protocol, runtime_checkable

logger = logging.getLogger(__name__)

# ---- 基础类型别名 ----
APIResponse: TypeAlias = Dict[str, Any]
EventHandler: TypeAlias = Callable[[Dict[str, Any]], Awaitable[None]]
MessageSegmentType = Dict[str, Any]


# ==================== 客户端接口 ====================

@runtime_checkable
class IClient(Protocol):
    """客户端 Protocol —— 定义所有客户端必须实现的方法签名"""

    @property
    def connected(self) -> bool:
        ...

    async def connect(self, max_retries: Optional[int] = None) -> bool:
        ...

    async def disconnect(self, force: bool = False) -> None:
        ...

    async def call_api(
        self,
        action: str,
        params: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> APIResponse:
        ...


# ==================== 连接事件监听器接口 ====================

class IConnectionEventListener:
    """连接事件监听器接口 —— 观察 WebSocket 连接状态变化"""

    async def on_connected(self) -> None:
        ...

    async def on_disconnected(self) -> None:
        ...

    async def on_reconnecting(self, attempt: int) -> None:
        ...

    async def on_reconnect_success(self) -> None:
        ...

    async def on_reconnect_failed(self, error: Exception) -> None:
        ...
