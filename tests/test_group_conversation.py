"""
群聊对话记忆管理器测试
"""
import unittest
import os
import shutil
import threading
import uuid
from unittest.mock import patch

from joha.managers.group_conversation import GroupConversationManager


# 使用项目内的固定测试目录
TEST_BASE = os.path.join(os.path.dirname(__file__), "_test_tmp")


class TestGroupConversationManager(unittest.TestCase):
    def setUp(self):
        self._tmpdir = os.path.join(TEST_BASE, str(uuid.uuid4()))
        os.makedirs(self._tmpdir, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self._tmpdir):
            shutil.rmtree(self._tmpdir, ignore_errors=True)

    def _make_mgr(self):
        mgr = GroupConversationManager()
        # 直接 mock _path 方法，让它写入测试目录
        original_path = mgr._path
        def mock_path(group_id):
            safe = str(group_id).replace("/", "_").replace("\\", "_")
            return os.path.join(self._tmpdir, f"group_{safe}.json")
        mgr._path = mock_path
        return mgr

    def test_add_and_get_context(self):
        mgr = self._make_mgr()
        mgr.add_user_message("g_test_ctx", "u1", "hello")
        mgr.add_bot_reply("g_test_ctx", "hi")
        ctx = mgr.get_context("g_test_ctx", limit=5)
        self.assertEqual(len(ctx), 2)
        self.assertEqual(ctx[0]["role"], "user")
        self.assertIn("u1", ctx[0]["content"])
        self.assertEqual(ctx[1]["role"], "assistant")

    def test_message_id_dedup(self):
        mgr = self._make_mgr()
        mgr.add_user_message("g_test_dedup", "u1", "first", message_id="m1")
        mgr.add_user_message("g_test_dedup", "u1", "first", message_id="m1")
        msgs = mgr.get_recent_messages("g_test_dedup", limit=10)
        self.assertEqual(len(msgs), 1)

    def test_auto_trim(self):
        mgr = self._make_mgr()
        for i in range(510):
            mgr.add_user_message("g_test_trim", f"u{i%3}", f"msg{i}")
        msgs = mgr._load("g_test_trim")
        self.assertLessEqual(len(msgs), 500)

    def test_thread_safety(self):
        mgr = self._make_mgr()
        errors = []
        def worker(uid):
            try:
                for i in range(20):
                    mgr.add_user_message("g_test_thread", uid, f"msg-{uid}-{i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(f"u{i}",)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertFalse(errors)
        msgs = mgr._load("g_test_thread")
        self.assertEqual(len(msgs), 100)


class TestGroupMemoryManager(unittest.TestCase):
    def setUp(self):
        self._tmpdir = os.path.join(TEST_BASE, str(uuid.uuid4()))
        os.makedirs(self._tmpdir, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self._tmpdir):
            shutil.rmtree(self._tmpdir, ignore_errors=True)

    def _make_mgr(self):
        import joha.managers.group_memory as mod
        mod.MEMORY_DIR = self._tmpdir
        from joha.managers.group_memory import GroupMemoryManager
        return GroupMemoryManager()

    def test_add_and_get_fact(self):
        mgr = self._make_mgr()
        added = mgr.add_fact("g_mem_add", "用户喜欢猫")
        self.assertTrue(added)
        dup = mgr.add_fact("g_mem_add", "用户喜欢猫")
        self.assertFalse(dup)

    def test_remove_fact(self):
        mgr = self._make_mgr()
        mgr.add_fact("g_mem_rm", "fact1")
        mgr.add_fact("g_mem_rm", "fact2")
        ok = mgr.remove_fact("g_mem_rm", "fact1")
        self.assertTrue(ok)
        dup = mgr.remove_fact("g_mem_rm", "fact1")
        self.assertFalse(dup)

    def test_get_context_prompt(self):
        mgr = self._make_mgr()
        mgr.add_fact("g_mem_prompt", "这是一个测试群")
        mgr.update_topics("g_mem_prompt", ["AI", "编程"])
        prompt = mgr.get_context_prompt("g_mem_prompt")
        self.assertIn("AI", prompt)
        self.assertIn("这是一个测试群", prompt)

    def test_get_memory_block(self):
        mgr = self._make_mgr()
        mgr.add_fact("g_mem_block", "test")
        block = mgr.get_memory_block("g_mem_block")
        self.assertIn("test", block)
        self.assertIn("群聊记忆", block)


def clean_test_tmp():
    """清理测试临时目录"""
    if os.path.exists(TEST_BASE):
        shutil.rmtree(TEST_BASE, ignore_errors=True)


if __name__ == "__main__":
    clean_test_tmp()
    unittest.main()
