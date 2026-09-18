from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ServiceCostProfile:
    service_id: str
    may_charge_money: bool
    note: str = ""


class PaidServiceBlocked(RuntimeError):
    pass


def assert_service_allowed(
    profile: ServiceCostProfile,
    *,
    allow_paid_services: bool,
) -> None:
    """Prevent accidental use of services that may create a bill."""
    if profile.may_charge_money and not allow_paid_services:
        raise PaidServiceBlocked(
            f"{profile.service_id} is marked as potentially paid and is blocked by "
            "YT SMB's zero-paid-services policy. Change allow_paid_services only "
            "if you intentionally want to permit paid providers."
        )
