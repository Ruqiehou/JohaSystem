"""
事件分发器实现
负责事件的注册、管理和分发，降低模块间耦合，全部采用 TypedDict 强类型
"""

from __future__ import annotations

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, List, Optional, TypedDict, Union

from joha.adapter.protocol.interfaces import IEventDispatcher

logger = logging.getLogger(__name__)

# ---- TypedDict ----

class HandlerInfo(TypedDict):
    """单个事件处理器的元信息"""
    handler: Callable[..., Any]
    priority: int
    name: str
    is_async: bool
    call_count: int
    total_time: float


class DispatcherStats(TypedDict):
    """事件分发器性能统计"""
    total_dispatched: int
    total_processing_time: float
    avg_latency: float
    errors: int


class StatsSnapshot(TypedDict, total=False):
    """分发器统计快照（含 handlers 计数）"""
    total_dispatched: int
    total_processing_time: float
    avg_latency: float
    errors: int
    handlers: Dict[str, int]


# ---- 类型别名 ----
FilterFunc = Callable[[Dict[str, Any]], bool]


class EventDispatcher(IEventDispatcher):
    """事件分发器 —— 统一管理事件监听器和分发逻辑

    特性：
    - 支持异步 & 同步处理器
    - 支持事件优先级
    - 支持事件过滤
    - 提供性能统计
    """

    def __init__(self, max_workers: int = 4) -> None:
        super().__init__()
        self._handlers: Dict[str, List[HandlerInfo]] = {
            "group": [],
            "private": [],
            "notice": [],
            "request": [],
        }
        self._executor: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=max_workers)
        self._stats: DispatcherStats = {
            "total_dispatched": 0,
            "total_processing_time": 0.0,
            "avg_latency": 0.0,
            "errors": 0,
        }
        self._filters: Dict[str, List[FilterFunc]] = {}

    # ==================== 注册 / 注销 ====================

    def register_handler(
        self,
        event_type: str,
        handler: Callable[..., Any],
        priority: int = 0,
        name: Optional[str] = None,
    ) -> None:
        if event_type not in self._handlers:
            logger.warning(f"未知事件类型: {event_type}")
            return

        is_async: bool = asyncio.iscoroutinefunction(handler)
        resolved_name: str = name or getattr(handler, "__name__", "unknown")

        info: HandlerInfo = {
            "handler": handler,
            "priority": priority,
            "name": resolved_name,
            "is_async": is_async,
            "call_count": 0,
            "total_time": 0.0,
        }

        self._handlers[event_type].append(info)
        self._handlers[event_type].sort(key=lambda x: x["priority"], reverse=True)
        logger.debug(f"注册事件处理器: {event_type}.{resolved_name} (priority={priority})")

    def unregister_handler(self, event_type: str, handler: Callable[..., Any]) -> bool:
        if event_type not in self._handlers:
            return False

        for i, info in enumerate(self._handlers[event_type]):
            if info["handler"] is handler:
                removed: HandlerInfo = self._handlers[event_type].pop(i)
                logger.debug(f"注销事件处理器: {event_type}.{removed['name']}")
                return True
        return False

    # ==================== 过滤器 ====================

    def add_filter(self, event_type: str, filter_func: FilterFunc) -> None:
        if event_type not in self._filters:
            self._filters[event_type] = []
        self._filters[event_type].append(filter_func)
        logger.debug(f"添加事件过滤器: {event_type}")

    def remove_filter(self, event_type: str, filter_func: FilterFunc) -> bool:
        if event_type not in self._filters:
            return False
        if filter_func in self._filters[event_type]:
            self._filters[event_type].remove(filter_func)
            return True
        return False

    # ==================== 分发 ====================

    async def dispatch(self, event_type: str, data: Dict[str, Any]) -> None:
        if event_type not in self._handlers:
            raise ValueError(f"未知事件类型: {event_type}")

        if event_type in self._filters:
            for f in self._filters[event_type]:
                try:
                    if not f(data):
                        logger.debug(f"事件被过滤: {event_type}")
                        return
                except Exception as e:
                    logger.error(f"过滤器执行失败: {e}")

        handlers: List[HandlerInfo] = self._handlers[event_type]
        if not handlers:
            return

        self._stats["total_dispatched"] += 1
        start_time: float = time.perf_counter()

        tasks = [self._execute_handler(h, data, event_type) for h in handlers]

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for r in results:
                if isinstance(r, Exception):
                    self._stats["errors"] += 1
                    logger.error(f"事件处理器执行失败: {r}")

        elapsed: float = time.perf_counter() - start_time
        self._stats["total_processing_time"] += elapsed
        self._stats["avg_latency"] = (
            self._stats["total_processing_time"] / self._stats["total_dispatched"]
        )

    async def _execute_handler(
        self,
        handler_info: HandlerInfo,
        data: Dict[str, Any],
        event_type: str,
    ) -> Any:
        handler: Callable[..., Any] = handler_info["handler"]
        name: str = handler_info["name"]
        is_async: bool = handler_info["is_async"]

        t0: float = time.perf_counter()

        try:
            if is_async:
                result: Any = await handler(data)
            else:
                loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    self._executor,
                    lambda: handler(data),
                )

            handler_info["call_count"] += 1
            handler_info["total_time"] += time.perf_counter() - t0
            return result

        except Exception as e:
            logger.error(f"事件处理器 {event_type}.{name} 执行失败: {e}", exc_info=True)
            raise

    # ==================== 查询 / 统计 ====================

    def get_handler_count(self, event_type: Optional[str] = None) -> int:
        if event_type is None:
            return sum(len(h) for h in self._handlers.values())
        return len(self._handlers.get(event_type, []))

    def get_stats(self) -> StatsSnapshot:
        snap: StatsSnapshot = {
            "total_dispatched": self._stats["total_dispatched"],
            "total_processing_time": self._stats["total_processing_time"],
            "avg_latency": self._stats["avg_latency"],
            "errors": self._stats["errors"],
            "handlers": {
                et: len(hl)
                for et, hl in self._handlers.items()
            },
        }
        return snap

    def reset_stats(self) -> None:
        self._stats = {
            "total_dispatched": 0,
            "total_processing_time": 0.0,
            "avg_latency": 0.0,
            "errors": 0,
        }

    def close(self) -> None:
        self._executor.shutdown(wait=False)
        logger.info("事件分发器已关闭")


# ==================== 子类 ====================

class PriorityEventDispatcher(EventDispatcher):
    """优先级事件分发器 —— 在 EventDispatcher 基础上增加更精细的优先级控制"""

    def __init__(self, max_workers: int = 4) -> None:
        super().__init__(max_workers)
        self._priority_groups: Dict[int, List[str]] = {}

    def register_handler(
        self,
        event_type: str,
        handler: Callable[..., Any],
        priority: int = 0,
        name: Optional[str] = None,
    ) -> None:
        super().register_handler(event_type, handler, priority, name)

        resolved_name: str = name or getattr(handler, "__name__", "unknown")
        if priority not in self._priority_groups:
            self._priority_groups[priority] = []
        self._priority_groups[priority].append(f"{event_type}.{resolved_name}")

    def get_handlers_by_priority(self, priority: int) -> List[str]:
        return self._priority_groups.get(priority, [])

    def get_all_priorities(self) -> List[int]:
        return sorted(self._priority_groups.keys(), reverse=True)
