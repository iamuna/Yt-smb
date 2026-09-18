from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shorts_factory.pipeline import BuildRequest, create_short
SMOKE_DIR = ROOT / "temp" / "ci-smoke"
SOURCE_DIR = SMOKE_DIR / "sources"
ARTIFACT_DIR = ROOT / "artifacts"


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        args,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(args)}\n{result.stderr}"
        )
    return result


def make_source(path: Path, color: str, seconds: int = 5) -> None:
    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c={color}:s=1280x720:r=30:d={seconds}",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:sample_rate=44100",
            "-shortest",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            str(path),
        ]
    )


def main() -> None:
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise RuntimeError("FFmpeg/ffprobe are required for the smoke test.")

    shutil.rmtree(SMOKE_DIR, ignore_errors=True)
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    make_source(SOURCE_DIR / "clip-1.mp4", "0x243447")
    make_source(SOURCE_DIR / "clip-2.mp4", "0x415a77")
    make_source(SOURCE_DIR / "clip-3.mp4", "0x778da9")

    result = create_short(
        BuildRequest(
            source_folder=SOURCE_DIR,
            hook="YT SMB REAL RENDER TEST",
            script=(
                "This video was generated automatically by the YT SMB rendering "
                "pipeline during a real Windows smoke test. If you can watch this, "
                "the editor, vertical crop, hook card, captions, and final MP4 "
                "encoding all worked."
            ),
            voice="default",
            target_seconds=12,
            use_voice=True,
            captions=True,
            allow_paid_services=False,
        )
    )

    demo = ARTIFACT_DIR / "yt-smb-demo.mp4"
    shutil.copy2(result.output_path, demo)

    probe = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height,codec_name,pix_fmt",
            "-show_entries",
            "format=duration,size",
            "-of",
            "json",
            str(demo),
        ]
    )
    metadata = json.loads(probe.stdout)
    stream = metadata["streams"][0]
    fmt = metadata["format"]

    assert int(stream["width"]) == 1080, metadata
    assert int(stream["height"]) == 1920, metadata
    assert stream["codec_name"] == "h264", metadata
    assert float(fmt["duration"]) >= 10.0, metadata
    assert int(fmt["size"]) > 50_000, metadata

    (ARTIFACT_DIR / "yt-smb-demo-metadata.json").write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )
    print(f"Rendered demo: {demo}")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
