from __future__ import annotations

from .base import SourceProvider
from .pexels import PexelsProvider


# ADD NEW SOURCE PROVIDERS HERE.
# A provider only needs to implement SourceProvider and be registered below.
_PROVIDERS: dict[str, type[SourceProvider]] = {
    "pexels": PexelsProvider,
}


def available_source_providers() -> dict[str, str]:
    return {
        provider_id: provider_type.display_name
        for provider_id, provider_type in _PROVIDERS.items()
    }


def get_source_provider(provider_id: str) -> SourceProvider:
    try:
        provider_type = _PROVIDERS[provider_id]
    except KeyError as exc:
        known = ", ".join(sorted(_PROVIDERS)) or "(none)"
        raise RuntimeError(
            f"Unknown media source provider '{provider_id}'. Available: {known}"
        ) from exc
    return provider_type()
