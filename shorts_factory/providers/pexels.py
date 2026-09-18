from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

import requests

from ..cost_policy import ServiceCostProfile
from .base import SourceAsset, SourceProvider


class PexelsProvider(SourceProvider):
    provider_id = "pexels"
    display_name = "Pexels"
    cost_profile = ServiceCostProfile(
        service_id="pexels",
        may_charge_money=False,
        note=(
            "Configured as a free source provider. External provider terms and "
            "quotas can change, so failures must stop rather than fall back to a "
            "paid service."
        ),
    )
    requires_api_key = True

    @staticmethod
    def _best_video_file(video: dict) -> dict | None:
        files = video.get("video_files") or []
        usable = [
            item
            for item in files
            if item.get("link")
            and item.get("file_type", "").startswith("video/")
        ]
        if not usable:
            return None

        portrait = [
            item
            for item in usable
            if (item.get("height") or 0) >= (item.get("width") or 0)
        ]
        candidates = portrait or usable
        candidates.sort(
            key=lambda item: abs((item.get("height") or 1080) - 1920)
            + abs((item.get("width") or 720) - 1080)
        )
        return candidates[0]

    def fetch_broll(
        self,
        *,
        search_terms: list[str],
        api_key: str,
        destination: Path,
        max_clips: int = 6,
    ) -> list[SourceAsset]:
        if not api_key.strip() or not search_terms:
            return []

        destination.mkdir(parents=True, exist_ok=True)
        headers = {"Authorization": api_key.strip()}
        assets: list[SourceAsset] = []
        seen_ids: set[int] = set()

        for term in search_terms:
            if len(assets) >= max_clips:
                break

            response = requests.get(
                "https://api.pexels.com/v1/videos/search",
                headers=headers,
                params={
                    "query": term,
                    "orientation": "portrait",
                    "size": "medium",
                    "per_page": 5,
                },
                timeout=20,
            )
            if response.status_code == 401:
                raise RuntimeError("Pexels API key was rejected.")
            response.raise_for_status()

            for video in response.json().get("videos", []):
                video_id = int(video.get("id") or 0)
                if not video_id or video_id in seen_ids:
                    continue

                selected = self._best_video_file(video)
                if not selected:
                    continue

                link = selected["link"]
                suffix = Path(urlparse(link).path).suffix.lower() or ".mp4"
                if suffix not in {".mp4", ".mov", ".m4v"}:
                    suffix = ".mp4"

                output = destination / f"pexels-{video_id}{suffix}"
                with requests.get(link, stream=True, timeout=60) as download:
                    download.raise_for_status()
                    with output.open("wb") as handle:
                        for chunk in download.iter_content(chunk_size=1024 * 512):
                            if chunk:
                                handle.write(chunk)

                user = video.get("user") or {}
                assets.append(
                    SourceAsset(
                        path=output,
                        provider=self.display_name,
                        creator=str(user.get("name") or "Pexels creator"),
                        source_url=str(
                            video.get("url") or "https://www.pexels.com/"
                        ),
                        license_note="Pexels source; verify current provider terms.",
                    )
                )
                seen_ids.add(video_id)
                if len(assets) >= max_clips:
                    break

        return assets
