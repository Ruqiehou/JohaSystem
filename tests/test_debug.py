"""
群聊对话记忆管理器测试（调试版）
"""
import unittest
import os
import tempfile
import shutil

from joha.managers.group_conversation import GroupConversationManager


class TestGroupConversationManagerDebug(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_debug(self):
        import joha.managers.group_conversation as mod
        mod.CONVERSATIONS_DIR = self._tmpdir
        mgr = GroupConversationManager()
        
        # Debug: check what directory the manager is using
        print(f"\n_tempdir: {self._tmpdir}")
        print(f"mod.CONVERSATIONS_DIR: {mod.CONVERSATIONS_DIR}")
        print(f"mgr._path('g_test'): {mgr._path('g_test')}")
        
        # Check if file exists before test
        path = mgr._path("g_test_ctx")
        print(f"File exists before: {os.path.exists(path)}")
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                print(f"File content before: {f.read()}")
        
        mgr.add_user_message("g_test_ctx", "u1", "hello")
        mgr.add_bot_reply("g_test_ctx", "hi")
        
        # Check file after adding
        print(f"File exists after: {os.path.exists(path)}")
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                print(f"File content after: {f.read()}")
        
        ctx = mgr.get_context("g_test_ctx", limit=5)
        print(f"Context length: {len(ctx)}")
        for i, m in enumerate(ctx):
            print(f"  [{i}] {m['role']}: {m['content'][:50]}")
        
        self.assertEqual(len(ctx), 2)


if __name__ == "__main__":
    unittest.main()
