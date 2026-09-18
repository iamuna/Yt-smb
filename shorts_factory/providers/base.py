from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from ..cost_policy import ServiceCostProfile


@dataclass
class SourceAsset:
    path: Path
    provider: str
    creator: str
    source_url: str
    license_note: str = ""


class SourceProvider(ABC):
    """Interface every online B-roll provider must implement."""

    provider_id: str
    display_name: str
    cost_profile: ServiceCostProfile
    requires_api_key: bool = True

    @abstractmethod
    def fetch_broll(
        self,
        *,
        search_terms: list[str],
        api_key: str,
        destination: Path,
        max_clips: int = 6,
    ) -> list[SourceAsset]:
        raise NotImplementedError
