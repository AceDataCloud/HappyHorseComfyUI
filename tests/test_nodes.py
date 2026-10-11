"""ComfyUI model choices and native video shape."""

import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "happy_horse_comfy", ROOT / "__init__.py", submodule_search_locations=[str(ROOT)]
)
package = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = package
spec.loader.exec_module(package)
nodes = sys.modules["happy_horse_comfy.nodes"]


class HappyHorseNodeTests(unittest.TestCase):
    def test_all_seven_dify_models_are_in_the_correct_action(self):
        classes = (nodes.AceHappyHorseTextToVideo, nodes.AceHappyHorseImageToVideo,
                   nodes.AceHappyHorseReferenceToVideo, nodes.AceHappyHorseVideoEdit)
        choices = [set(cls.INPUT_TYPES()["required"]["model"][0]) for cls in classes]
        self.assertEqual([len(choice) for choice in choices], [2, 2, 2, 1])
        self.assertEqual(len(set.union(*choices)), 7)

    def test_submission_shows_task_id_without_claiming_video(self):
        with patch.object(nodes, "submit", return_value=("pending", "task-123", "", "trace-123")):
            value = nodes.AceHappyHorseTextToVideo().run(
                "horse", "happyhorse-1.1-t2v", "720P", "16:9", 5, False, -1)
        self.assertEqual(value["result"], ("pending", "task-123", "", "trace-123"))
        self.assertIn("task-123", " ".join(value["ui"]["text"]))

    def test_loader_returns_native_video_object(self):
        fake_package = types.ModuleType("comfy_api")
        fake_latest = types.ModuleType("comfy_api.latest")
        class FakeVideo:
            def __init__(self, raw):
                self.raw = raw
        fake_latest.VideoFromFile = FakeVideo
        with patch.dict(sys.modules, {"comfy_api": fake_package, "comfy_api.latest": fake_latest}):
            with patch.object(nodes, "download_video", return_value=b"video-bytes"):
                (video,) = nodes.AceHappyHorseLoadVideo().run("https://cdn.acedata.cloud/a.mp4")
        self.assertEqual(video.raw.getvalue(), b"video-bytes")


if __name__ == "__main__":
    unittest.main()
