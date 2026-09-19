from __future__ import annotations

from pathlib import Path

from .base import VideoGenerator
from .comfyui_wan import ComfyUIWanGenerator


_GENERATORS: dict[str, type[VideoGenerator]] = {
    "comfyui_wan22": ComfyUIWanGenerator,
}


def available_video_generators() -> dict[str, str]:
    return {
        provider_id: provider_type.display_name
        for provider_id, provider_type in _GENERATORS.items()
    }


def get_video_generator(
    provider_id: str,
    *,
    base_url: str = "http://127.0.0.1:8188",
    workflow_file: Path | None = None,
) -> VideoGenerator:
    try:
        provider_type = _GENERATORS[provider_id]
    except KeyError as exc:
        known = ", ".join(sorted(_GENERATORS)) or "(none)"
        raise RuntimeError(
            f"Unknown video generator '{provider_id}'. Available: {known}"
        ) from exc

    if provider_type is ComfyUIWanGenerator:
        return ComfyUIWanGenerator(
            base_url=base_url,
            workflow_file=workflow_file,
        )
    return provider_type()
