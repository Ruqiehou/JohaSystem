"""
消息段构建器
用于构建 NapCat / OneBot 数组格式的消息
"""

from __future__ import annotations

import json
from typing import Any, Dict, Union

from joha.adapter.transport.interfaces import MessageSegmentType


class MessageSegment:
    """消息段构建器 —— 用于构建 NapCat 数组格式的消息"""

    @staticmethod
    def text(content: str) -> MessageSegmentType:
        return {"type": "text", "data": {"text": content}}

    @staticmethod
    def image(file: str, summary: str = "") -> MessageSegmentType:
        data: Dict[str, Any] = {"file": file}
        if summary:
            data["summary"] = summary
        return {"type": "image", "data": data}

    @staticmethod
    def at(qq: Union[int, str]) -> MessageSegmentType:
        return {"type": "at", "data": {"qq": str(qq)}}

    @staticmethod
    def reply(message_id: int) -> MessageSegmentType:
        return {"type": "reply", "data": {"id": message_id}}

    @staticmethod
    def face(face_id: int) -> MessageSegmentType:
        return {"type": "face", "data": {"id": face_id}}

    @staticmethod
    def dice() -> MessageSegmentType:
        return {"type": "dice", "data": {}}

    @staticmethod
    def rps() -> MessageSegmentType:
        return {"type": "rps", "data": {}}

    @staticmethod
    def json_data(data: Union[Dict[str, Any], str]) -> MessageSegmentType:
        if isinstance(data, dict):
            data = json.dumps(data, ensure_ascii=False)
        return {"type": "json", "data": {"data": data}}
