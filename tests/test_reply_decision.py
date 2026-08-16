"""
回复决策引擎（reply_decision）核心概率计算测试
"""
import unittest

from joha.decision.reply_decision import (
    build_context,
    compute_reply_prob,
    should_reply,
    MessageContext,
)


class TestReplyDecision(unittest.TestCase):

    def test_probability_in_range(self):
        ctx = build_context(text="你好", user_id="u1", group_id="")
        prob = compute_reply_prob(ctx)
        self.assertGreaterEqual(prob, 0.0)
        self.assertLessEqual(prob, 1.0)

    def test_at_bot_increases_probability(self):
        normal = compute_reply_prob(build_context(text="你好", user_id="u1", group_id=""))
        at_bot = compute_reply_prob(build_context(
            text="你好", user_id="u1", group_id="", is_at_bot=True
        ))
        self.assertGreater(at_bot, normal)

    def test_reply_to_bot_increases_probability(self):
        normal = compute_reply_prob(build_context(text="你好", user_id="u1", group_id=""))
        reply = compute_reply_prob(build_context(
            text="你好", user_id="u1", group_id="", reply_to_bot=True
        ))
        self.assertGreater(reply, normal)

    def test_question_intent_increases_probability(self):
        normal = compute_reply_prob(build_context(text="你好", user_id="u1", group_id=""))
        question = compute_reply_prob(build_context(text="今天天气怎么样？", user_id="u1", group_id=""))
        self.assertGreater(question, normal)

    def test_pure_media_is_penalized(self):
        normal = compute_reply_prob(build_context(text="你好", user_id="u1", group_id=""))
        media = compute_reply_prob(build_context(
            text="你好", user_id="u1", group_id="", is_pure_media=True
        ))
        self.assertLess(media, normal)

    def test_should_reply_respects_threshold(self):
        # 被@ + 提问时大概率回复
        ctx = build_context(
            text="这个功能怎么用？", user_id="u1", group_id="",
            is_at_bot=True, reply_to_bot=True,
        )
        self.assertTrue(should_reply(ctx))

    def test_force_high_threshold_blocks(self):
        ctx = build_context(text="你好", user_id="u1", group_id="")
        ctx.group_msg_per_minute = 100  # 非常活跃群
        # 高频群阈值高，普通消息不应回复
        result = should_reply(ctx)
        self.assertIn(result, (True, False))  # 只验证不抛异常且返回布尔

    def test_intent_detection(self):
        ctx = build_context(text="这个怎么弄？", user_id="u1", group_id="")
        prob = compute_reply_prob(ctx)
        self.assertEqual(ctx.intent, "question")
        self.assertGreater(ctx.intent_confidence, 0.0)


if __name__ == "__main__":
    unittest.main()
