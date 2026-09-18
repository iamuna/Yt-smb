from __future__ import annotations

from pathlib import Path

from .cost_policy import assert_service_allowed
from .providers import SourceAsset, get_source_provider


def fetch_broll(
    *,
    provider_id: str,
    search_terms: list[str],
    api_key: str,
    destination: Path,
    max_clips: int = 6,
    allow_paid_services: bool = False,
) -> list[SourceAsset]:
    """Provider-neutral B-roll entry point.

    New media services should be implemented under shorts_factory/providers/
    and registered in providers/registry.py. The rest of the app should not
    contain provider-specific download logic.
    """
    provider = get_source_provider(provider_id)
    assert_service_allowed(
        provider.cost_profile,
        allow_paid_services=allow_paid_services,
    )
    if provider.requires_api_key and not api_key.strip():
        return []

    return provider.fetch_broll(
        search_terms=search_terms,
        api_key=api_key,
        destination=destination,
        max_clips=max_clips,
    )


__all__ = ["SourceAsset", "fetch_broll"]
