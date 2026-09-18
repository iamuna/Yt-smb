import unittest

from shorts_factory.providers import (
    available_source_providers,
    get_source_provider,
)


class ProviderRegistryTests(unittest.TestCase):
    def test_pexels_is_registered(self):
        providers = available_source_providers()
        self.assertIn("pexels", providers)

    def test_current_pexels_adapter_is_not_marked_paid(self):
        provider = get_source_provider("pexels")
        self.assertFalse(provider.cost_profile.may_charge_money)

    def test_unknown_provider_does_not_silently_fallback(self):
        with self.assertRaises(RuntimeError):
            get_source_provider("this-provider-does-not-exist")


if __name__ == "__main__":
    unittest.main()
