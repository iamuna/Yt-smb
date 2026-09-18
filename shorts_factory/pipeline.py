from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .config import OUTPUT_DIR, TEMP_DIR
from .editor import build_vertical_short
from .tts import synthesize_voice
from .utils import find_video_files, safe_slug


@dataclass
class BuildRequest:
    source_folder: Path
    hook: str
    script: str
    voice: str
    target_seconds: int
    use_voice: bool = True


@dataclass
class BuildResult:
    output_path: Path
    clip_count: int


def create_short(request: BuildRequest) -> BuildResult:
    clips = find_video_files(request.source_folder)
    if not clips:
        raise RuntimeError(
            "No video clips found. Add MP4/MOV/MKV/WebM files to the selected folder."
        )

    clips = clips[:25]
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    slug = safe_slug(request.hook)
    job_temp = TEMP_DIR / f"{stamp}-{slug}"
    job_temp.mkdir(parents=True, exist_ok=True)

    narration = None
    if request.use_voice and request.script.strip():
        narration = job_temp / "voice.mp3"
        synthesize_voice(request.script.strip(), request.voice, narration)

    output = OUTPUT_DIR / f"{stamp}-{slug}.mp4"
    build_vertical_short(
        clips=clips,
        output_path=output,
        temp_dir=job_temp,
        hook=request.hook.strip() or "Watch this",
        target_seconds=request.target_seconds,
        narration_path=narration,
    )
    return BuildResult(output_path=output, clip_count=len(clips))
