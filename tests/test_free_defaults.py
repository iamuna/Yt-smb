import unittest

from shorts_factory.config import DEFAULT_SETTINGS


class FreeDefaultsTests(unittest.TestCase):
    def test_paid_services_are_blocked_by_default(self):
        self.assertFalse(DEFAULT_SETTINGS["allow_paid_services"])

    def test_local_ai_is_default(self):
        self.assertEqual(DEFAULT_SETTINGS["ai_provider"], "ollama")
        self.assertNotIn("gpt-", DEFAULT_SETTINGS["ai_model"].lower())

    def test_local_voice_is_default(self):
        self.assertEqual(DEFAULT_SETTINGS["voice"], "default")


if __name__ == "__main__":
    unittest.main()
