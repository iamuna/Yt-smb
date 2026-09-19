import json
import tempfile
import unittest
from pathlib import Path

from shorts_factory.config import DEFAULT_SETTINGS, DEFAULT_VIDEO_WORKFLOW
from shorts_factory.video_generators import (
    VideoGenerationRequest,
    available_video_generators,
    get_video_generator,
)
from shorts_factory.video_generators.comfyui_wan import ComfyUIWanGenerator


class VideoGeneratorRegistryTests(unittest.TestCase):
    def test_generic_local_generator_is_registered(self):
        providers = available_video_generators()
        self.assertIn("comfyui_local_video", providers)

    def test_default_generator_is_local_and_free(self):
        self.assertEqual(
            DEFAULT_SETTINGS["video_generator_provider"],
            "comfyui_local_video",
        )
        provider = get_video_generator("comfyui_local_video")
        self.assertFalse(provider.cost_profile.may_charge_money)

    def test_old_wan_id_remains_compatible(self):
        provider = get_video_generator("comfyui_wan22")
        self.assertFalse(provider.cost_profile.may_charge_money)

    def test_unknown_generator_does_not_fallback(self):
        with self.assertRaises(RuntimeError):
            get_video_generator("does-not-exist")

    def test_workflow_placeholders_are_replaced(self):
        graph = {
            "1": {
                "class_type": "Example",
                "inputs": {
                    "prompt": "__YT_SMB_PROMPT__",
                    "negative": "__YT_SMB_NEGATIVE__",
                    "width": "__YT_SMB_WIDTH__",
                    "height": "__YT_SMB_HEIGHT__",
                    "frames": "__YT_SMB_FRAMES__",
                    "fps": "__YT_SMB_FPS__",
                    "seed": "__YT_SMB_SEED__",
                },
            }
        }

        with tempfile.TemporaryDirectory() as directory:
            workflow = Path(directory) / "workflow.json"
            workflow.write_text(json.dumps(graph), encoding="utf-8")
            provider = ComfyUIWanGenerator(workflow_file=workflow)

            request = VideoGenerationRequest(
                prompt="realistic CCTV parking lot",
                negative_prompt="cartoon",
                width=480,
                height=832,
                frames=81,
                fps=16,
                seed=1234,
            )
            loaded = provider._load_workflow(request)
            inputs = loaded["1"]["inputs"]

            self.assertEqual(inputs["prompt"], request.prompt)
            self.assertEqual(inputs["negative"], request.negative_prompt)
            self.assertEqual(inputs["width"], 480)
            self.assertEqual(inputs["height"], 832)
            self.assertEqual(inputs["frames"], 81)
            self.assertEqual(inputs["fps"], 16)
            self.assertEqual(inputs["seed"], 1234)


    def test_bundled_workflow_exists_and_has_all_placeholders(self):
        self.assertTrue(DEFAULT_VIDEO_WORKFLOW.is_file())
        data = json.loads(DEFAULT_VIDEO_WORKFLOW.read_text(encoding="utf-8"))
        serialized = json.dumps(data)

        for placeholder in (
            "__YT_SMB_PROMPT__",
            "__YT_SMB_NEGATIVE__",
            "__YT_SMB_WIDTH__",
            "__YT_SMB_HEIGHT__",
            "__YT_SMB_FRAMES__",
            "__YT_SMB_FPS__",
            "__YT_SMB_SEED__",
        ):
            self.assertIn(placeholder, serialized)

        classes = {
            node.get("class_type")
            for node in data.values()
            if isinstance(node, dict)
        }
        self.assertIn("UNETLoader", classes)
        self.assertIn("Wan22ImageToVideoLatent", classes)
        self.assertIn("KSampler", classes)
        self.assertIn("VAEDecode", classes)
        self.assertIn("CreateVideo", classes)
        self.assertIn("SaveVideo", classes)


if __name__ == "__main__":
    unittest.main()
