from __future__ import annotations

import random
from pathlib import Path

from .config import OUTPUT_DIR
from .video_generators import VideoGenerationRequest, get_video_generator


def generate_video(
    *,
    provider_id: str,
    prompt: str,
    negative_prompt: str,
    base_url: str,
    workflow_file: Path | None,
    width: int,
    height: int,
    seconds: int,
    fps: int,
    seed: int | None = None,
    allow_paid_services: bool = False,
):
    if seed is None or seed < 0:
        seed = random.randint(0, 2**31 - 1)

    frames = max(17, int(seconds * fps) + 1)
    generator = get_video_generator(
        provider_id,
        base_url=base_url,
        workflow_file=workflow_file,
    )
    return generator.generate(
        VideoGenerationRequest(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            frames=frames,
            fps=fps,
            seed=seed,
            output_dir=OUTPUT_DIR / "generated",
        ),
        allow_paid_services=allow_paid_services,
    )


def generator_ready(
    *,
    provider_id: str,
    base_url: str,
    workflow_file: Path | None,
) -> bool:
    generator = get_video_generator(
        provider_id,
        base_url=base_url,
        workflow_file=workflow_file,
    )
    return generator.ready()
