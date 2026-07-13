"""
意图识别器（纯规则版）
基于正则的意图分类，无 LLM 依赖
"""
import re
from typing import Dict


class IntentClassifier:
    """纯规则意图识别器"""

    def classify_intent(self, text: str) -> Dict[str, any]:
        """规则驱动的意图识别"""
        text_lower = text.lower().strip()
        if not text_lower:
            return {'intent': 'spam', 'confidence': 0.8, 'details': {}}

        if re.search(r'[?？]', text):
            return {'intent': 'question', 'confidence': 0.6, 'details': {}}
        elif re.search(r'^\s*[#!/]', text):
            return {'intent': 'command', 'confidence': 0.7, 'details': {}}
        elif any(word in text_lower for word in ['开心', '难过', '生气', '喜欢', '讨厌']):
            return {'intent': 'emotion', 'confidence': 0.5, 'details': {}}
        elif len(set(text)) < len(text) * 0.3 and len(text) > 5:
            return {'intent': 'spam', 'confidence': 0.7, 'details': {}}
        else:
            return {'intent': 'chat', 'confidence': 0.4, 'details': {}}


# 全局单例
_intent_classifier_instance = None


def get_intent_classifier() -> IntentClassifier:
    global _intent_classifier_instance
    if _intent_classifier_instance is None:
        _intent_classifier_instance = IntentClassifier()
    return _intent_classifier_instance


def reload_intent_classifier():
    global _intent_classifier_instance
    _intent_classifier_instance = None
    return get_intent_classifier()


# 向后兼容代理
class _IntentClassifierProxy:
    def __getattr__(self, name):
        return getattr(get_intent_classifier(), name)

intent_classifier = _IntentClassifierProxy()
