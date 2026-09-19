from __future__ import annotations

import random
from pathlib import Path

from .config import OUTPUT_DIR
from .utils import executable_available, run_process, safe_slug
from .video_generators import VideoGenerationRequest, VideoGenerationResult, get_video_generator


def _finish_for_shorts(result: VideoGenerationResult) -> VideoGenerationResult:
    """Normalize generated media to a real 1080x1920 H.264 Short."""
    if not executable_available("ffmpeg"):
        return result

    source = result.path
    if not source.exists():
        return result

    slug = safe_slug(result.prompt)[:42]
    destination = OUTPUT_DIR / "generated" / f"{slug}-{result.seed}-9x16.mp4"
    destination.parent.mkdir(parents=True, exist_ok=True)

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(source),
        "-vf",
        (
            "scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,"
            "fps=30,"
            "format=yuv420p"
        ),
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "20",
        "-movflags",
        "+faststart",
        str(destination),
    ]
    render = run_process(command)
    if render.returncode != 0:
        raise RuntimeError(
            "AI video was generated, but 9:16 finishing failed: "
            + (render.stderr.strip() or "FFmpeg failed")
        )

    metadata = dict(result.metadata)
    metadata.update(
        {
            "raw_generated_path": str(source),
            "finished_width": 1080,
            "finished_height": 1920,
            "finished_format": "mp4",
        }
    )
    return VideoGenerationResult(
        path=destination,
        provider=result.provider,
        prompt=result.prompt,
        seed=result.seed,
        metadata=metadata,
    )


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
    # Wan video lengths work best as 4n+1. Round upward when needed.
    remainder = (frames - 1) % 4
    if remainder:
        frames += 4 - remainder

    generator = get_video_generator(
        provider_id,
        base_url=base_url,
        workflow_file=workflow_file,
    )
    result = generator.generate(
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
    return _finish_for_shorts(result)


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
