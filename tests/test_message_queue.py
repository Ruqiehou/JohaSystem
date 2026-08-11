"""
消息队列测试
"""
import unittest
import asyncio
import time
import os
import shutil
import uuid

from joha.core.message_queue import MessageQueueManager, MergedMessage

TEST_BASE = os.path.join(os.path.dirname(__file__), "_test_tmp")


class TestMessageQueue(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self._tmpdir = os.path.join(TEST_BASE, str(uuid.uuid4()))
        os.makedirs(self._tmpdir, exist_ok=True)

    def tearDown(self):
        self.loop.close()
        if os.path.exists(self._tmpdir):
            shutil.rmtree(self._tmpdir, ignore_errors=True)

    async def _add(self, queue, uid, gid, msg, **kw):
        return await queue.add_message(uid, gid, msg, **kw)

    def _flush(self, queue, uid, gid):
        results = []
        while True:
            merged = self.loop.run_until_complete(queue.force_process(uid, gid))
            if not merged:
                break
            results.append(merged)
        return results

    def test_basic_merge(self):
        queue = MessageQueueManager(merge_window=1.0)
        queue.min_messages_to_merge = 2
        self.loop.run_until_complete(self._add(queue, "u1", "g1", "a"))
        self.loop.run_until_complete(self._add(queue, "u1", "g1", "b"))
        results = self._flush(queue, "u1", "g1")
        self.assertEqual(len(results), 1)
        self.assertIn("a", results[0].merged_text)
        self.assertIn("b", results[0].merged_text)

    def test_single_message_timeout(self):
        """单条消息应在超时后被处理，不再永久搁置"""
        queue = MessageQueueManager(merge_window=0.1)
        queue.min_messages_to_merge = 2
        # 添加单条消息，不立即 flush
        self.loop.run_until_complete(self._add(queue, "u1", "g1", "alone"))
        # 等待超时
        time.sleep(0.2)
        # 添加第二条消息，应触发包含 alone 的合并
        merged = self.loop.run_until_complete(self._add(queue, "u1", "g1", "trigger"))
        self.assertIsNotNone(merged)
        self.assertIn("alone", merged.merged_text)

    def test_max_queue_size(self):
        """达到最大队列大小后，最早消息应立即处理"""
        queue = MessageQueueManager(merge_window=60.0)
        queue.max_queue_size = 3
        for i in range(4):
            self.loop.run_until_complete(self._add(queue, f"u{i}", "g1", f"m{i}"))
        results = self._flush(queue, "u0", "g1")
        self.assertTrue(len(results) >= 1)

    def test_message_dedup(self):
        """队列会自动合并重复内容"""
        queue = MessageQueueManager(merge_window=60.0)
        self.loop.run_until_complete(self._add(queue, "u1", "g1", "dup"))
        self.loop.run_until_complete(self._add(queue, "u1", "g1", "dup"))
        results = self._flush(queue, "u1", "g1")
        self.assertEqual(len(results), 1)


class TestMergedMessage(unittest.TestCase):
    def test_count_property(self):
        msg = MergedMessage(
            user_id="u1", group_id="g1", merged_text="a\nb",
            messages=["a", "b"],
            timestamp=0.0, last_timestamp=0.0,
        )
        self.assertEqual(msg.count, 2)


def clean_test_tmp():
    if os.path.exists(TEST_BASE):
        shutil.rmtree(TEST_BASE, ignore_errors=True)


if __name__ == "__main__":
    clean_test_tmp()
    unittest.main()
