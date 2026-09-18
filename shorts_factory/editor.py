from __future__ import annotations

import os
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .utils import ffprobe_duration, run_process


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    windir = Path(os.environ.get("WINDIR", r"C:\Windows"))
    for name in ("arialbd.ttf", "segoeuib.ttf", "arial.ttf"):
        candidate = windir / "Fonts" / name
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def _make_hook_overlay(text: str, output_path: Path) -> Path:
    image = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    wrapped = textwrap.wrap(text.strip() or "Watch this", width=24)[:4]
    font = _font(70)
    lines = "\n".join(wrapped)

    bbox = draw.multiline_textbbox(
        (0, 0),
        lines,
        font=font,
        spacing=12,
        align="center",
        stroke_width=3,
    )
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    pad_x = 55
    pad_y = 38
    left = max(45, (1080 - text_w) // 2 - pad_x)
    top = 120
    right = min(1035, (1080 + text_w) // 2 + pad_x)
    bottom = top + text_h + pad_y * 2

    draw.rounded_rectangle(
        (left, top, right, bottom),
        radius=34,
        fill=(0, 0, 0, 175),
    )
    draw.multiline_text(
        ((1080 - text_w) // 2, top + pad_y),
        lines,
        font=font,
        fill=(255, 255, 255, 255),
        spacing=12,
        align="center",
        stroke_width=3,
        stroke_fill=(0, 0, 0, 255),
    )
    image.save(output_path)
    return output_path


def _normalize_segment(source: Path, output: Path, seconds: float) -> None:
    result = run_process(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(source),
            "-t",
            f"{seconds:.3f}",
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
            str(output),
        ]
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Could not prepare {source.name}: "
            + (result.stderr.strip() or "FFmpeg failed")
        )


def _write_concat_file(paths: list[Path], concat_file: Path) -> None:
    lines = []
    for path in paths:
        escaped = str(path.resolve()).replace("'", "'\\''")
        lines.append(f"file '{escaped}'")
    concat_file.write_text("\n".join(lines), encoding="utf-8")


def build_vertical_short(
    clips: list[Path],
    output_path: Path,
    temp_dir: Path,
    hook: str,
    target_seconds: int = 35,
    narration_path: Path | None = None,
) -> Path:
    if not clips:
        raise ValueError("No source clips were found.")

    temp_dir.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Build short normalized pieces so mixed resolutions/codecs concatenate reliably.
    segments: list[Path] = []
    elapsed = 0.0
    index = 0

    usable: list[tuple[Path, float]] = []
    for clip in clips:
        try:
            duration = ffprobe_duration(clip)
        except Exception:
            continue
        if duration >= 0.7:
            usable.append((clip, duration))

    if not usable:
        raise RuntimeError("The selected folder contains no readable video clips.")

    while elapsed < target_seconds and index < 40:
        source, duration = usable[index % len(usable)]
        remaining = target_seconds - elapsed
        segment_seconds = min(4.0, duration, remaining)
        if segment_seconds < 0.5:
            break

        segment = temp_dir / f"segment-{index:03d}.mp4"
        _normalize_segment(source, segment, segment_seconds)
        actual = min(ffprobe_duration(segment), segment_seconds)
        if actual > 0.3:
            segments.append(segment)
            elapsed += actual
        index += 1

    if not segments:
        raise RuntimeError("No usable segments could be rendered.")

    concat_file = temp_dir / "segments.txt"
    _write_concat_file(segments, concat_file)

    joined = temp_dir / "joined.mp4"
    concat = run_process(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-c",
            "copy",
            str(joined),
        ]
    )
    if concat.returncode != 0:
        raise RuntimeError(concat.stderr.strip() or "Could not join video segments.")

    video_duration = min(ffprobe_duration(joined), float(target_seconds))
    hook_png = _make_hook_overlay(hook, temp_dir / "hook.png")

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(joined),
        "-loop",
        "1",
        "-i",
        str(hook_png),
    ]

    narration_index = None
    if narration_path and narration_path.exists():
        narration_index = 2
        command += ["-i", str(narration_path)]

    command += [
        "-filter_complex",
        (
            "[0:v][1:v]overlay=0:0:"
            "enable='between(t,0,3.8)'[v]"
        ),
        "-map",
        "[v]",
    ]

    if narration_index is not None:
        command += [
            "-map",
            f"{narration_index}:a:0",
            "-af",
            f"apad=whole_dur={video_duration:.3f}",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
        ]
    else:
        command += ["-an"]

    command += [
        "-t",
        f"{video_duration:.3f}",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "20",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(output_path),
    ]

    result = run_process(command)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Final FFmpeg render failed.")

    return output_path
