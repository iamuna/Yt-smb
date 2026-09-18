# Adding or replacing a B-roll provider

YT SMB deliberately isolates third-party stock/media services behind a provider interface.

## Files involved

- `shorts_factory/providers/base.py` — interface and `SourceAsset`.
- `shorts_factory/providers/registry.py` — provider registry.
- `shorts_factory/sources.py` — provider-neutral caller.
- `shorts_factory/secrets.py` — per-provider API keys.
- `app.py` — reads provider names from the registry automatically.

## Provider contract

Create a module under `shorts_factory/providers/`.

Example skeleton:

```python
from pathlib import Path

from ..cost_policy import ServiceCostProfile
from .base import SourceAsset, SourceProvider


class ExampleProvider(SourceProvider):
    provider_id = "example"
    display_name = "Example"
    requires_api_key = True

    cost_profile = ServiceCostProfile(
        service_id="example",
        may_charge_money=False,
        note="Explain current cost assumptions here.",
    )

    def fetch_broll(
        self,
        *,
        search_terms: list[str],
        api_key: str,
        destination: Path,
        max_clips: int = 6,
    ) -> list[SourceAsset]:
        # Search the provider.
        # Download only media permitted by its license/terms.
        # Return local file paths plus provenance metadata.
        return []
```

Then register it in `shorts_factory/providers/registry.py`:

```python
_PROVIDERS = {
    "pexels": PexelsProvider,
    "example": ExampleProvider,
}
```

The Settings dropdown will then expose the provider without rewriting the automation pipeline.

## Cost requirement

Every provider declares a `ServiceCostProfile`.

If a provider can create usage charges, set:

```python
may_charge_money=True
```

YT SMB's default cost policy will then block it because `allow_paid_services=False`.

Never mislabel a paid service as free just to make it run.

## Licensing/provenance requirement

Each downloaded asset should return:

- local path
- provider name
- creator/uploader name when available
- source URL
- a short license/provenance note

Provider terms can change. Keep provider-specific terms out of the generic pipeline and update the provider module/documentation when necessary.

## No silent fallback

If the configured provider fails, return an actionable error or continue with local clips where appropriate.

Do **not** silently switch to another provider that can incur charges.
