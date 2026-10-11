"""Action/model, task, billing-boundary, and media safety checks."""

import os
import unittest
from unittest.mock import Mock, patch

import client


class HappyHorseClientTests(unittest.TestCase):
    def setUp(self):
        env = patch.dict(os.environ, {"ACEDATACLOUD_API_KEY": "test-key"})
        env.start()
        self.addCleanup(env.stop)

    @patch("client.requests.post")
    def test_text_generation_submits_once_with_11_model(self, post):
        post.return_value = Mock(status_code=200)
        post.return_value.json.return_value = {"task_id": "task-123", "trace_id": "trace-123"}
        result = client.submit("generate", "happyhorse-1.1-t2v", "A horse runs", duration=5)
        self.assertEqual(result, ("pending", "task-123", "", "trace-123"))
        post.assert_called_once()
        self.assertEqual(post.call_args.args[0], "https://api.acedata.cloud/happyhorse/videos")
        self.assertEqual(post.call_args.kwargs["json"]["action"], "generate")

    @patch("client.requests.post")
    def test_action_model_mismatch_and_private_reference_fail_before_payment(self, post):
        with self.assertRaises(ValueError):
            client.submit("generate", "happyhorse-1.1-i2v", "A horse")
        with self.assertRaises(ValueError):
            client.submit("image_to_video", "happyhorse-1.1-i2v", "", image_url="https://127.0.0.1/a.png")
        post.assert_not_called()

    @patch("client.requests.post")
    def test_reference_and_edit_payloads_are_action_specific(self, post):
        post.return_value = Mock(status_code=200)
        post.return_value.json.return_value = {"task_id": "task-123"}
        client.submit("reference_to_video", "happyhorse-1.0-r2v", "Keep the character",
                      image_urls='["https://example.org/a.png"]')
        first = post.call_args.kwargs["json"]
        self.assertEqual(first["image_urls"], ["https://example.org/a.png"])
        self.assertNotIn("video_url", first)
        client.submit("video_edit", "happyhorse-1.0-video-edit", "Change the scene",
                      video_url="https://example.org/a.mp4", audio_setting="origin")
        second = post.call_args.kwargs["json"]
        self.assertEqual(second["video_url"], "https://example.org/a.mp4")
        self.assertEqual(second["audio_setting"], "origin")
        self.assertNotIn("duration", second)

    @patch("client.requests.post")
    def test_submission_timeout_never_retries_or_leaks_key(self, post):
        post.side_effect = client.requests.Timeout("Bearer test-key")
        with self.assertRaises(client.HappyHorseError) as caught:
            client.submit("generate", "happyhorse-1.1-t2v", "A horse")
        post.assert_called_once()
        self.assertNotIn("test-key", str(caught.exception))

    @patch("client.requests.post")
    def test_pending_preview_does_not_claim_terminal_video(self, post):
        post.return_value = Mock(status_code=200)
        post.return_value.json.return_value = {
            "id": "task-123", "finished_at": None,
            "response": {"data": [{"state": "pending", "video_url": "https://cdn.acedata.cloud/a.mp4"}]},
        }
        self.assertEqual(client.retrieve_once("task-123")[:3], ("pending", "task-123", ""))

    @patch("client.requests.post")
    def test_retrieve_terminal_video_from_documented_response(self, post):
        post.return_value = Mock(status_code=200)
        post.return_value.json.return_value = {
            "id": "task-123", "finished_at": 1769262774.423,
            "response": {"success": True, "data": [{"state": "succeeded",
                "video_url": "https://platform2.cdn.acedata.cloud/happyhorse/a.mp4"}]},
        }
        self.assertEqual(client.retrieve_once("task-123")[:3],
                         ("succeeded", "task-123", "https://platform2.cdn.acedata.cloud/happyhorse/a.mp4"))

    @patch("client.requests.post")
    def test_batch_is_read_only_and_preserves_each_id(self, post):
        post.return_value = Mock(status_code=200)
        post.return_value.json.return_value = {"items": [
            {"id": "a", "finished_at": None, "response": None},
            {"id": "b", "finished_at": 1, "response": {"data": [
                {"state": "succeeded", "video_url": "https://cdn.acedata.cloud/b.mp4"}]}}
        ]}
        rows = client.retrieve_batch('["a","b"]')
        self.assertEqual([row["status"] for row in rows], ["pending", "succeeded"])
        self.assertEqual(post.call_args.kwargs["json"], {"action": "retrieve_batch", "ids": ["a", "b"]})

    @patch("client.requests.get")
    def test_video_loader_rejects_non_ace_hosts(self, get):
        for url in ("https://127.0.0.1/a.mp4", "https://cdn.acedata.cloud.evil.test/a.mp4",
                    "http://cdn.acedata.cloud/a.mp4"):
            with self.assertRaises(client.HappyHorseError):
                client.download_video(url)
        get.assert_not_called()


if __name__ == "__main__":
    unittest.main()
