from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
TEMP = ROOT / "temp" / "real-cctv-demo"
ARTIFACTS = ROOT / "artifacts"

SOURCE_URL = (
    "https://upload.wikimedia.org/wikipedia/commons/6/63/"
    "2019_Bnei_Ayish_IF2_tornado_security_camera_video.webm"
)


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
            f"Command failed: {' '.join(args)}\n{result.stderr[-5000:]}"
        )
    return result


def download_source(destination: Path) -> None:
    with requests.get(
        SOURCE_URL,
        stream=True,
        timeout=120,
        headers={"User-Agent": "YT-SMB-demo/0.3"},
    ) as response:
        response.raise_for_status()
        with destination.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)


def main() -> None:
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise RuntimeError("FFmpeg/ffprobe are required.")

    TEMP.mkdir(parents=True, exist_ok=True)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)

    source = TEMP / "source.webm"
    output = ARTIFACTS / "real-moving-cctv-parking-lot.mp4"
    metadata_file = ARTIFACTS / "real-moving-cctv-parking-lot-metadata.json"

    download_source(source)

    # This is one continuous section of real moving CCTV footage.
    # We only alter the presentation: lower FPS, light grain, security-camera HUD.
    filter_chain = (
        "fps=12,"
        "scale=960:-2,"
        "eq=contrast=1.08:brightness=-0.02:saturation=0.42,"
        "noise=alls=5:allf=t+u,"
        "drawbox=x=0:y=0:w=iw:h=64:color=black@0.42:t=fill,"
        "drawtext=text='CAM 07  DEALERSHIP LOT':"
        "fontcolor=white:fontsize=26:x=18:y=16,"
        "drawtext=text='REC':fontcolor=white:fontsize=24:x=w-78:y=16,"
        "drawbox=x=w-24:y=22:w=9:h=9:color=red@0.92:t=fill,"
        "drawtext=text='MOTION ALERT':"
        "enable='between(t,5.5,13.5)':"
        "fontcolor=white:fontsize=24:x=18:y=h-48"
    )

    run(
        [
            "ffmpeg",
            "-y",
            "-ss",
            "2",
            "-t",
            "20",
            "-i",
            str(source),
            "-vf",
            filter_chain,
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "24",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "96k",
            "-movflags",
            "+faststart",
            str(output),
        ]
    )

    probe = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "stream=codec_name,width,height,r_frame_rate",
            "-show_entries",
            "format=duration,size",
            "-of",
            "json",
            str(output),
        ]
    )
    metadata = json.loads(probe.stdout)

    streams = metadata.get("streams", [])
    video = next(item for item in streams if item.get("codec_name") == "h264")
    assert int(video["width"]) == 960, metadata
    assert float(metadata["format"]["duration"]) >= 19.0, metadata
    assert int(metadata["format"]["size"]) > 200_000, metadata

    metadata["source"] = {
        "type": "public-domain automated security-camera footage",
        "url": SOURCE_URL,
        "description": (
            "2019 Bnei Ayish IF2 tornado security camera video; "
            "Wikimedia Commons marks the automated-camera footage public domain."
        ),
    }
    metadata_file.write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )

    print(f"Created continuous CCTV demo: {output}")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
