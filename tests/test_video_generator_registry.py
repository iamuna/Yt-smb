import unittest

from shorts_factory.video_generators import (
    available_video_generators,
    get_video_generator,
)


class VideoGeneratorRegistryTests(unittest.TestCase):
    def test_local_wan_generator_is_registered(self):
        providers = available_video_generators()
        self.assertIn("comfyui_wan22", providers)

    def test_default_generator_is_not_marked_paid(self):
        provider = get_video_generator("comfyui_wan22")
        self.assertFalse(provider.cost_profile.may_charge_money)

    def test_unknown_generator_does_not_fallback(self):
        with self.assertRaises(RuntimeError):
            get_video_generator("does-not-exist")


if __name__ == "__main__":
    unittest.main()
