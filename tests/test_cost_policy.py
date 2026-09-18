import unittest

from shorts_factory.cost_policy import (
    PaidServiceBlocked,
    ServiceCostProfile,
    assert_service_allowed,
)


class CostPolicyTests(unittest.TestCase):
    def test_free_service_is_allowed(self):
        assert_service_allowed(
            ServiceCostProfile("free-test", may_charge_money=False),
            allow_paid_services=False,
        )

    def test_paid_service_is_blocked(self):
        with self.assertRaises(PaidServiceBlocked):
            assert_service_allowed(
                ServiceCostProfile("paid-test", may_charge_money=True),
                allow_paid_services=False,
            )


if __name__ == "__main__":
    unittest.main()
