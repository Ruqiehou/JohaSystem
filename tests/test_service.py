"""
service.py pipeline 阶段单元测试
"""
import unittest
import asyncio
from unittest.mock import AsyncMock, patch

from joha.core.service import MessageService, MessageContext


class TestMessageServiceStages(unittest.TestCase):
    def setUp(self):
        self.service = MessageService()

    def test_learn_stage(self):
        ctx = MessageContext(user_id="u_svc_learn", message="hello")
        self.service._learn_stage(ctx)
        from joha.managers.history_manager import history_manager
        h = history_manager.load_history("u_svc_learn", group_id=None)
        self.assertTrue(len(h) >= 1)

    def test_context_stage_builds_messages(self):
        ctx = MessageContext(user_id="u_svc_ctx", group_id="g_svc_ctx", message="你好")
        with patch("joha.managers.history_manager.history_manager.load_history", return_value=[]):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self.service._context_stage(ctx))
            finally:
                loop.close()
                asyncio.set_event_loop(None)
        self.assertTrue(result)
        self.assertTrue(len(ctx.context_messages) >= 2)
        self.assertEqual(ctx.context_messages[0]["role"], "system")

    def test_vision_stage_skips_unsupported_model(self):
        ctx = MessageContext(user_id="u_svc_vis", message="test", images=["https://img"])
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(self.service._vision_stage(ctx))
        finally:
            loop.close()
            asyncio.set_event_loop(None)
        self.assertTrue(result)
        self.assertEqual(ctx.images, [])

    def test_generate_stage_failure(self):
        ctx = MessageContext(user_id="u_svc_gen", message="test")
        ctx.context_messages = [{"role": "system", "content": "test"}]
        with patch("joha.ai.generator.generator.chat", new_callable=AsyncMock, return_value=None):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self.service._generate_stage(ctx))
            finally:
                loop.close()
                asyncio.set_event_loop(None)
        self.assertFalse(result)

    def test_record_stage_writes_conversation(self):
        ctx = MessageContext(
            user_id="u_svc_rec", group_id="g_svc_rec", message="hi",
            response="hello"
        )
        self.service._record_stage(ctx)
        from joha.managers.group_conversation import group_conversation
        conv = group_conversation.get_context("g_svc_rec", limit=10)
        self.assertTrue(len(conv) >= 2)

    def test_get_stats_structure(self):
        stats = self.service.get_stats()
        self.assertIn("uptime", stats)
        self.assertIn("total_messages", stats)
        self.assertIn("generated_replies", stats)


class TestMessageContext(unittest.TestCase):
    def test_defaults(self):
        ctx = MessageContext()
        self.assertEqual(ctx.user_id, "")
        self.assertIsNone(ctx.group_id)
        self.assertEqual(ctx.message, "")
        self.assertFalse(ctx.should_reply)

    def test_merged_flag(self):
        ctx = MessageContext(
            messages=["a", "b"], merged_text="a\nb", is_merged=True
        )
        self.assertTrue(ctx.is_merged)
        self.assertEqual(len(ctx.messages), 2)


if __name__ == "__main__":
    unittest.main()
