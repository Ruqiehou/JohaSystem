"""
统一消息构建器
将 service._handle_active_mode 和 generator._build_messages 的重复逻辑合并
"""
from typing import List, Dict, Optional
from joha.managers.personas import get_persona, get_persona_by_group
from joha.managers.history_manager import history_manager
from joha.managers.style_learner import style_learner
from joha.config.logger import tprint


class MessageBuilder:

    def __init__(self):
        self.tool_registry = None

    def build(
        self,
        user_id: str,
        message: str,
        images: list = None,
        persona_name: str = "joha",
        history: list = None,
        include_style: bool = True,
        include_rag: bool = True,
        rag_top_k: int = 3,
        rag_min_score: float = 0.15,
        history_limit: int = 10,
        group_id: Optional[str] = None,
    ) -> List[Dict]:
        images = images or []

        if group_id and persona_name == "joha":
            persona = get_persona_by_group(group_id)
        else:
            persona = get_persona(persona_name)
        system_prompt = persona.get("system_prompt",
            "你是一个真实的大学生，说话自然随意，像普通人聊天。回复简短自然，不超过20字。")

        # 检测用户是否称呼了AI的名字，如果是则强化自我认同
        if self._check_name_call(message):
            system_prompt += "\n\n【重要】用户正在称呼你的名字！你必须以第一人称明确回应自己的身份，表现出自我认同。例如：'对啊，我就是joha/马苏'、'嗯，我在呢'等自然的回应方式。"
        
        # 检测是否为合并消息（多条消息）
        if '\n' in message:
            message_lines = [line.strip() for line in message.split('\n') if line.strip()]
            if len(message_lines) > 1:
                system_prompt += f"\n\n【注意】用户连续发送了{len(message_lines)}条消息，这些是同一时间段内的连续发言。请综合考虑所有消息的语境进行回复，不要逐条回应。"

        if include_style:
            style_prompt = style_learner.get_user_style_prompt(user_id)
            if style_prompt:
                system_prompt += "\n\n" + style_prompt

        # 注入工具描述（如果 ToolRegistry 已初始化且有工具）
        if self.tool_registry:
            tool_desc = self.tool_registry.get_tool_descriptions()
            if tool_desc:
                system_prompt += "\n\n" + tool_desc

        context_messages = [{"role": "system", "content": system_prompt}]

        if history is None:
            history = history_manager.load_history(user_id, group_id=group_id)
        if isinstance(history, list):
            for h in history[-history_limit:]:
                if isinstance(h, dict):
                    if h.get("message"):
                        context_messages.append({"role": "user", "content": h["message"]})

        if images:
            content_parts = []
            prompt_text = message if message else "看看这张图，用一句话描述你觉得有趣的地方"
            content_parts.append({"type": "text", "text": prompt_text})
            for img_url in images:
                content_parts.append({"type": "image_url", "image_url": {"url": img_url}})
            context_messages.append({"role": "user", "content": content_parts})
        else:
            context_messages.append({"role": "user", "content": message})

        return context_messages

    def build_system_prompt(self, user_id: str, persona_name: str = "joha",
                            include_style: bool = True, group_id: Optional[str] = None) -> str:
        if group_id and persona_name == "joha":
            persona = get_persona_by_group(group_id)
        else:
            persona = get_persona(persona_name)
        system_prompt = persona.get("system_prompt",
            "你是一个真实的大学生，说话自然随意，像普通人聊天。回复简短自然，不超过20字。")

        if include_style:
            style_prompt = style_learner.get_user_style_prompt(user_id)
            if style_prompt:
                system_prompt += "\n\n" + style_prompt

        return system_prompt

    def _check_name_call(self, message: str) -> bool:
        """检测用户是否称呼了AI的名字"""
        if not message:
            return False
        
        # 从配置中获取bot昵称列表
        from joha.decision.reply_decision import reply_cfg
        bot_names = reply_cfg.bot_nicknames
        
        # 检查消息中是否包含任何bot昵称
        message_lower = message.lower()
        for name in bot_names:
            if name.lower() in message_lower:
                return True
        
        return False


message_builder = MessageBuilder()
