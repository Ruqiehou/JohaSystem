"""joha.adapter.core.client → joha.adapter.transport.client 兼容重导出"""

from joha.adapter.transport.client import NapCatClient
from joha.adapter.transport.interfaces import IClient, IConnectionEventListener, MessageSegmentType

__all__ = ["NapCatClient", "IClient", "IConnectionEventListener", "MessageSegmentType"]
