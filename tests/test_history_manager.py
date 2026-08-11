"""
历史记录管理器并发安全测试
"""
import unittest
import os
import shutil
import threading
import uuid
from unittest.mock import patch

from joha.managers.history_manager import HistoryManager

# 使用项目内的固定测试目录
TEST_BASE = os.path.join(os.path.dirname(__file__), "_test_tmp")


class TestHistoryManagerConcurrency(unittest.TestCase):
    def setUp(self):
        self._tmpdir = os.path.join(TEST_BASE, str(uuid.uuid4()))
        os.makedirs(self._tmpdir, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self._tmpdir):
            shutil.rmtree(self._tmpdir, ignore_errors=True)

    def _make_mgr(self):
        import joha.managers.history_manager as mod
        mod.STORAGE_DIR = self._tmpdir
        return HistoryManager()

    def test_add_message_basic(self):
        mgr = self._make_mgr()
        mgr.add_message("u_hist_basic", "hello", group_id="g_hist_basic")
        history = mgr.load_history("u_hist_basic", group_id="g_hist_basic")
        self.assertTrue(len(history) >= 1)

    def test_group_isolation(self):
        mgr = self._make_mgr()
        mgr.add_message("u_hist_iso", "msg1", group_id="g_hist_iso1")
        mgr.add_message("u_hist_iso", "msg2", group_id="g_hist_iso2")
        h1 = mgr.load_history("u_hist_iso", group_id="g_hist_iso1")
        h2 = mgr.load_history("u_hist_iso", group_id="g_hist_iso2")
        self.assertEqual(len(h1), 1)
        self.assertEqual(len(h2), 1)

    def test_concurrent_writes_no_corruption(self):
        mgr = self._make_mgr()
        errors = []
        def worker(uid):
            try:
                for i in range(20):
                    mgr.add_message(uid, f"msg-{uid}-{i}", group_id="g_hist_conc")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(f"u_hist_{i}",)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertFalse(errors)
        for i in range(5):
            h = mgr.load_history(f"u_hist_{i}", group_id="g_hist_conc")
            self.assertEqual(len(h), 20)

    def test_clear_history(self):
        mgr = self._make_mgr()
        mgr.add_message("u_hist_clear", "msg1", group_id="g_hist_clear")
        mgr.add_message("u_hist_clear", "msg2", group_id="g_hist_clear")
        ok = mgr.clear_history("u_hist_clear", group_id="g_hist_clear")
        self.assertTrue(ok)
        h = mgr.load_history("u_hist_clear", group_id="g_hist_clear")
        self.assertEqual(len(h), 0)


class TestGroupStateManager(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mktemp(suffix=".json")
        import joha.decision.group_state as mod
        mod.GROUP_STATE_FILE = self._tmp
        from joha.decision.group_state import GroupStateManager
        self.mgr = GroupStateManager()

    def tearDown(self):
        import joha.decision.group_state as mod
        mod.GROUP_STATE_FILE = mod.GROUP_STATE_FILE
        if os.path.exists(self._tmp):
            os.remove(self._tmp)

    def test_record_and_get(self):
        self.mgr.record_message("g_state_1", "u1", "hello")
        state = self.mgr.get("g_state_1")
        self.assertIsNotNone(state)
        self.assertEqual(state.total_messages, 1)

    def test_record_bot_reply(self):
        self.mgr.record_bot_reply("g_state_2", "hi")
        state = self.mgr.get("g_state_2")
        self.assertEqual(state.bot_replies, 1)
        self.assertEqual(state.total_messages, 1)

    def test_record_feedback(self):
        self.mgr.record_feedback("g_state_3", positive=True)
        state = self.mgr.get("g_state_3")
        self.assertEqual(state.positive_feedbacks, 1)

    def test_get_stats(self):
        self.mgr.record_message("g_state_4", "u1", "a")
        self.mgr.record_message("g_state_4", "u2", "b")
        stats = self.mgr.get_stats()
        self.assertEqual(stats["total_groups"], 1)
        self.assertEqual(stats["total_messages"], 2)

    def test_thread_safety_under_load(self):
        errors = []
        def worker(gid, uid):
            try:
                for i in range(20):
                    self.mgr.record_message(gid, uid, f"msg{i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=("g_state_5", f"u_state_{i}")) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertFalse(errors)
        state = self.mgr.get("g_state_5")
        self.assertEqual(state.total_messages, 100)


def clean_test_tmp():
    """清理测试临时目录"""
    if os.path.exists(TEST_BASE):
        shutil.rmtree(TEST_BASE, ignore_errors=True)


if __name__ == "__main__":
    clean_test_tmp()
    unittest.main()
