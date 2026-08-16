"""
消息构建器三层记忆测试
"""
import unittest
import os

from joha.core.message_builder import MessageBuilder


class TestMessageBuilder(unittest.TestCase):
    def setUp(self):
        self.builder = MessageBuilder()

    def test_basic_system_prompt(self):
        msgs = self.builder.build(user_id="u1", message="你好", persona_name="joha")
        self.assertEqual(msgs[0]["role"], "system")
        self.assertIn("joha", msgs[0]["content"])

    def test_history_injection(self):
        msgs = self.builder.build(
            user_id="u1", message="hello",
            history=[{"message": "旧消息"}], include_style=False
        )
        roles = [m["role"] for m in msgs]
        self.assertIn("user", roles)
        self.assertIn("system", roles)

    def test_image_message(self):
        msgs = self.builder.build(
            user_id="u1", message="看图",
            images=["https://example.com/img.png"],
            include_style=False
        )
        last = msgs[-1]
        self.assertEqual(last["role"], "user")
        self.assertIsInstance(last["content"], list)
        self.assertTrue(any(part.get("type") == "image_url" for part in last["content"]))

    def test_user_history_limit(self):
        history = [{"message": f"msg{i}"} for i in range(30)]
        msgs = self.builder.build(
            user_id="u1", message="最新",
            history=history, history_limit=10, include_style=False
        )
        user_msgs = [m for m in msgs if m["role"] == "user" and "msg" in m["content"]]
        self.assertLessEqual(len(user_msgs), 10)


if __name__ == "__main__":
    unittest.main()
