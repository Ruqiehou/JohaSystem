"""
决策引擎（总）v1.0
统一编排决策流水线：意图分析 → 命令检测 → 回复概率 → 动作分级 → 工具调度
各子模块（分）保持专注单一职责，由本引擎串联整合
"""
import time
from typing import Dict, Optional, Any
from dataclasses import dataclass, field

from joha.decision.reply_decision import (
    should_reply, build_context, MessageContext, compute_reply_prob,
)
from joha.decision.cooldown import cooldown_manager, CooldownManager
from joha.decision.group_state import group_state_manager
from joha.decision.intent_classifier import get_intent_classifier, IntentClassifier
from joha.config.logger import johalog_logger, tprint

# ==================== 命令分析器 (from command_analyzer.py) ====================

import json
from typing import Dict
from joha.ai.clients import create_client_from_provider
from joha.ai.providers import provider_manager, Provider
from joha.config.config_manager import config as config_manager


class CommandAnalyzer:
    """自然语言命令分析器"""

    def __init__(self):
        self.provider = None
        self._init_provider()

    def _init_provider(self):
        """初始化工具调用专用的 Provider"""
        tool_config = config_manager.get("tool_calling", {})
        if not tool_config.get("enabled", False):
            return

        provider_name = tool_config.get("provider_name", "")
        if provider_name:
            # 优先从 _available_configs 查找，支持独立密钥
            available = config_manager.get("intent_recognition._available_configs", {})
            conf = available.get(provider_name)
            if conf:
                self.provider = Provider(
                    name=provider_name,
                    role="tool_caller",
                    api_key=conf.get("api_key", ""),
                    base_url=conf.get("base_url", ""),
                    model=conf.get("model", "")
                )
            else:
                self.provider = provider_manager.get(provider_name)
        
        if not self.provider:
            self.provider = provider_manager.get_default("chat")

        if self.provider:
            self.client = create_client_from_provider(self.provider, client_type="chat", enable_tools=False)
            tprint("info", f"[CommandAnalyzer] 已加载: {self.provider.name} ({self.provider.model})")

    def analyze(self, text: str) -> Dict[str, any]:
        """
        分析用户输入，判断是否需要调用工具
        返回格式: {
            'action': 'chat' | 'search' | 'knowledge' | 'webpage',
            'query': str,
            'confidence': float
        }
        """
        if not self.provider:
            return {'action': 'chat', 'query': text, 'confidence': 1.0}

        prompt = f"""请分析以下用户输入的意图。如果用户想查询实时信息、新闻、天气或事实性知识，请选择 'search'。
如果用户想查找项目历史、过往对话或本地记录，请选择 'knowledge'。
如果用户提供了 URL 并希望了解内容，请选择 'webpage'。
否则选择 'chat'。

用户输入：{text}

只返回 JSON 格式：
{{"action": "chat/search/knowledge/webpage", "query": "提取出的搜索关键词或原话", "confidence": 0.9}}
"""
        messages = [{"role": "user", "content": prompt}]
        
        try:
            response = self.client.call_with_context(messages, temperature=0.1, max_tokens=100)
            response = response.strip()
            if response.startswith('```'):
                response = response.split('\n', 1)[-1].rsplit('\n', 1)[0]
            
            result = json.loads(response)
            return {
                'action': result.get('action', 'chat'),
                'query': result.get('query', text),
                'confidence': result.get('confidence', 0.5)
            }
        except Exception as e:
            tprint("warning", f"[CommandAnalyzer] 分析失败: {e}")
            return {'action': 'chat', 'query': text, 'confidence': 0.0}


# 全局实例
command_analyzer = CommandAnalyzer()


@dataclass
class EngineResult:
    """决策引擎输出结果"""
    should_reply: bool = False
    action_level: str = "ignore"
    short_reply: str = ""
    reply_text: str = ""

    probability: float = 0.0
    threshold: float = 0.0
    intent: str = "chat"
    intent_confidence: float = 0.0
    reasons: list = field(default_factory=list)

    tool_action: Optional[Dict] = None
    tool_response: Optional[str] = None
    needs_llm: bool = True

    _ctx: Optional[MessageContext] = None
    _mode: str = "passive"


class DecisionEngine:
    """决策引擎 — 总分架构的"总"

    对外仅暴露 process() 入口，内部编排完整的决策流水线。
    """

    def __init__(
        self,
        cooldown: CooldownManager = cooldown_manager,
        cmd_analyzer: CommandAnalyzer = command_analyzer,
        intent_cls: IntentClassifier = None,
    ):
        self.cooldown = cooldown
        self.command_analyzer = cmd_analyzer
        self.intent_classifier = intent_cls or get_intent_classifier()
        self._stats = {"total_calls": 0, "replied": 0, "skipped": 0}

    def process(
        self,
        text: str,
        user_id: str,
        group_id: str = "",
        is_at_bot: bool = False,
        reply_to_bot: bool = False,
        is_pure_media: bool = False,
        is_private: bool = False,
        group_mode: str = "passive",
        force_reply: bool = False,
        **kwargs,
    ) -> EngineResult:
        """
        完整决策流水线

        Args:
            text: 消息内容
            user_id: 用户 ID
            group_id: 群 ID
            is_at_bot: 是否 @机器人
            reply_to_bot: 是否回复机器人
            is_pure_media: 纯媒体消息
            is_private: 私聊
            group_mode: 群模式（active / passive）
            force_reply: 强制回复

        Returns:
            EngineResult 包含全部决策信息
        """
        self._stats["total_calls"] += 1
        result = EngineResult(_mode=group_mode)

        if group_mode != "active" and not force_reply:
            self._stats["skipped"] += 1
            return result

        ctx = build_context(
            text=text,
            user_id=user_id,
            group_id=group_id,
            is_at_bot=is_at_bot,
            reply_to_bot=reply_to_bot,
            is_pure_media=is_pure_media,
        )
        result._ctx = ctx

        result.tool_action = self._detect_command(ctx)

        prob = compute_reply_prob(ctx, self.cooldown)
        result.probability = prob
        result.intent = ctx.intent
        result.intent_confidence = ctx.intent_confidence

        decision = should_reply(ctx, self.cooldown)
        result.should_reply = decision

        self._log_decision(result, ctx)
        if result.should_reply:
            self._stats["replied"] += 1
        else:
            self._stats["skipped"] += 1

        return result

    def _detect_command(self, ctx: MessageContext) -> Optional[Dict]:
        """命令检测：先验斜杠命令，再走 AI 命令分析"""
        text = ctx.text

        if text.startswith("/"):
            return {"type": "slash", "command": text.split()[0], "args": text.split(" ", 1)[1] if " " in text else ""}

        if ctx.intent in {"command", "question"} and ctx.intent_confidence > 0.5:
            try:
                result = self.command_analyzer.analyze(text)
                if result.get("action") != "chat" and result.get("confidence", 0) > 0.6:
                    return result
            except Exception as e:
                tprint("warning", f"[决策引擎] 命令分析失败: {e}")

        return None

    def _execute_tool(self, tool_action: Dict) -> Optional[str]:
        """执行工具调用"""
        action_type = tool_action.get("type") or tool_action.get("action", "")
        query = tool_action.get("args") or tool_action.get("query", "")
        command = tool_action.get("command", "")

        if action_type == "slash" and command:
            from joha.core import get_tool_registry
            if query:
                return get_tool_registry().dispatch(command, query)
            return None

        from joha.tools import SearchTool, WebpageTool
        tool_map = {
            "search": lambda q: SearchTool().search(q),
            "webpage": lambda q: WebpageTool().fetch(q),
        }
        tool = tool_map.get(action_type)
        if tool and query:
            result = tool(query)
            return result if result else None

        return None

    def _log_decision(self, result: EngineResult, ctx: MessageContext):
        """记录决策日志"""
        tprint("info",
            f"[决策] 概率={result.probability:.3f} | "
            f"意图={result.intent}({result.intent_confidence:.2f}) | "
            f"{'✅ 回复' if result.should_reply else '❌ 跳过'}"
        )
        johalog_logger.debug(
            f"[回复决策] 概率={result.probability:.3f}, 意图={result.intent}, "
            f"决策={'✅回复' if result.should_reply else '❌不回复'}"
        )

    def get_stats(self) -> Dict:
        """获取引擎统计"""
        return {
            "total_calls": self._stats["total_calls"],
            "replied": self._stats["replied"],
            "skipped": self._stats["skipped"],
            "reply_rate": round(
                self._stats["replied"] / max(self._stats["total_calls"], 1), 3
            ),
        }

    def refresh(self):
        """刷新各子模块状态"""
        self.cooldown = cooldown_manager
        self.command_analyzer = command_analyzer
        self.intent_classifier = get_intent_classifier()


_engine_instance: Optional[DecisionEngine] = None


def get_decision_engine() -> DecisionEngine:
    """获取决策引擎（单例）"""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = DecisionEngine()
    return _engine_instance
