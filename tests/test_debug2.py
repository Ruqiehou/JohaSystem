"""
群聊对话记忆管理器测试（调试版）
"""
import unittest
import os
import shutil
import uuid

from joha.managers.group_conversation import GroupConversationManager

TEST_BASE = os.path.join(os.path.dirname(__file__), "_test_tmp")


class TestGroupConversationManagerDebug(unittest.TestCase):
    def setUp(self):
        self._tmpdir = os.path.join(TEST_BASE, str(uuid.uuid4()))
        os.makedirs(self._tmpdir, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self._tmpdir):
            shutil.rmtree(self._tmpdir, ignore_errors=True)

    def _make_mgr(self):
        mgr = GroupConversationManager()
        original_path = mgr._path
        def mock_path(group_id):
            safe = str(group_id).replace("/", "_").replace("\\", "_")
            result = os.path.join(self._tmpdir, f"group_{safe}.json")
            print(f"DEBUG _path({group_id}) -> {result}")
            return result
        mgr._path = mock_path
        return mgr

    def test_debug(self):
        mgr = self._make_mgr()
        print(f"DEBUG _tmpdir: {self._tmpdir}")
        print(f"DEBUG files in _tmpdir before: {os.listdir(self._tmpdir) if os.path.exists(self._tmpdir) else 'N/A'}")
        mgr.add_user_message("g_test_ctx", "u1", "hello")
        mgr.add_bot_reply("g_test_ctx", "hi")
        print(f"DEBUG files in _tmpdir after: {os.listdir(self._tmpdir)}")
        ctx = mgr.get_context("g_test_ctx", limit=5)
        print(f"DEBUG context length: {len(ctx)}")
        for i, m in enumerate(ctx):
            print(f"DEBUG   [{i}] {m['role']}: {m['content'][:50]}")
        self.assertEqual(len(ctx), 2)


if __name__ == "__main__":
    unittest.main()
