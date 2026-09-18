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


def _text_overlay(
    text: str,
    output_path: Path,
    *,
    font_size: int,
    top: int,
    wrap_width: int,
    max_lines: int,
    pad_x: int = 48,
    pad_y: int = 30,
) -> Path:
    image = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    font = _font(font_size)

    wrapped = textwrap.wrap(text.strip() or "Watch this", width=wrap_width)[:max_lines]
    lines = "\n".join(wrapped)
    bbox = draw.multiline_textbbox(
        (0, 0),
        lines,
        font=font,
        spacing=10,
        align="center",
        stroke_width=3,
    )
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    left = max(40, (1080 - text_w) // 2 - pad_x)
    right = min(1040, (1080 + text_w) // 2 + pad_x)
    bottom = top + text_h + pad_y * 2

    draw.rounded_rectangle(
        (left, top, right, bottom),
        radius=30,
        fill=(0, 0, 0, 185),
    )
    draw.multiline_text(
        ((1080 - text_w) // 2, top + pad_y),
        lines,
        font=font,
        fill=(255, 255, 255, 255),
        spacing=10,
        align="center",
        stroke_width=3,
        stroke_fill=(0, 0, 0, 255),
    )
    image.save(output_path)
    return output_path


def _make_hook_overlay(text: str, output_path: Path) -> Path:
    return _text_overlay(
        text,
        output_path,
        font_size=70,
        top=120,
        wrap_width=24,
        max_lines=4,
    )


def _caption_chunks(text: str, max_words: int = 6) -> list[str]:
    words = text.replace("\n", " ").split()
    chunks = []
    for index in range(0, len(words), max_words):
        chunk = " ".join(words[index : index + max_words]).strip()
        if chunk:
            chunks.append(chunk)
    return chunks[:24]


def _make_caption_overlays(
    text: str,
    duration: float,
    temp_dir: Path,
) -> list[tuple[Path, float, float]]:
    chunks = _caption_chunks(text)
    if not chunks or duration <= 0:
        return []

    total_words = max(1, sum(len(chunk.split()) for chunk in chunks))
    cursor = 0.0
    overlays: list[tuple[Path, float, float]] = []

    for index, chunk in enumerate(chunks):
        word_count = max(1, len(chunk.split()))
        chunk_duration = duration * word_count / total_words
        start = cursor
        end = duration if index == len(chunks) - 1 else min(duration, cursor + chunk_duration)
        cursor = end

        path = temp_dir / f"caption-{index:03d}.png"
        _text_overlay(
            chunk,
            path,
            font_size=62,
            top=1400,
            wrap_width=24,
            max_lines=3,
            pad_x=42,
            pad_y=24,
        )
        overlays.append((path, start, end))

    return overlays


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
    caption_text: str = "",
) -> Path:
    if not clips:
        raise ValueError("No source clips were found.")

    temp_dir.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)

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
        raise RuntimeError("The selected sources contain no readable video clips.")

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
    captions = _make_caption_overlays(caption_text, video_duration, temp_dir)

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

    for caption_path, _, _ in captions:
        command += ["-loop", "1", "-i", str(caption_path)]

    narration_index = None
    if narration_path and narration_path.exists():
        narration_index = 2 + len(captions)
        command += ["-i", str(narration_path)]

    filters = [
        "[0:v][1:v]overlay=0:0:enable='between(t,0,3.8)'[v1]"
    ]
    previous = "v1"

    for idx, (_, start, end) in enumerate(captions):
        input_index = 2 + idx
        output_label = f"v{idx + 2}"
        filters.append(
            f"[{previous}][{input_index}:v]overlay=0:0:"
            f"enable='between(t,{start:.3f},{end:.3f})'[{output_label}]"
        )
        previous = output_label

    command += [
        "-filter_complex",
        ";".join(filters),
        "-map",
        f"[{previous}]",
    ]

    if narration_index is not None:
        command += [
            "-map",
            f"{narration_index}:a:0",
            "-af",
            "apad",
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
