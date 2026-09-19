from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
INPUT_DIR = ROOT / "input"
OUTPUT_DIR = ROOT / "output"
TEMP_DIR = ROOT / "temp"
SETTINGS_FILE = DATA_DIR / "settings.json"

DEFAULT_SETTINGS = {
    "source_folder": str(INPUT_DIR),
    "voice": "default",
    "publish_enabled": False,
    "target_seconds": 35,
    "use_online_sources": True,
    "source_provider": "pexels",
    "auto_queue": True,
    "privacy_status": "private",
    "ai_provider": "ollama",
    "ai_model": "qwen2.5:3b",
    "ollama_base_url": "http://127.0.0.1:11434",
    "allow_paid_services": False,

    # Local AI video generation.
    "video_generator_provider": "comfyui_wan22",
    "comfyui_base_url": "http://127.0.0.1:8188",
    "video_workflow_file": "",
    "video_width": 480,
    "video_height": 832,
    "video_seconds": 5,
    "video_fps": 16,
    "video_negative_prompt": (
        "text, subtitles, watermark, logo, low quality, duplicate objects, "
        "deformed vehicles, unstable geometry, frame tearing"
    ),
}


def ensure_directories() -> None:
    for folder in (DATA_DIR, INPUT_DIR, OUTPUT_DIR, TEMP_DIR):
        folder.mkdir(parents=True, exist_ok=True)


def _migrate_settings(data: dict) -> dict:
    migrated = dict(data)

    # v0.2 compatibility.
    if "use_online_sources" not in migrated and "use_pexels" in migrated:
        migrated["use_online_sources"] = bool(migrated["use_pexels"])
    if "source_provider" not in migrated:
        migrated["source_provider"] = "pexels"

    old_model = str(migrated.get("ai_model", ""))
    if old_model.startswith("gpt-"):
        migrated["ai_model"] = "qwen2.5:3b"
        migrated["ai_provider"] = "ollama"

    old_voice = str(migrated.get("voice", ""))
    if old_voice.endswith("Neural"):
        migrated["voice"] = "default"

    # Cost safety: old configs never implicitly enable paid services.
    migrated.setdefault("allow_paid_services", False)

    # v0.4 video-generator defaults are local and provider-based.
    migrated.setdefault("video_generator_provider", "comfyui_wan22")
    migrated.setdefault("comfyui_base_url", "http://127.0.0.1:8188")
    migrated.setdefault("video_workflow_file", "")
    migrated.setdefault("video_width", 480)
    migrated.setdefault("video_height", 832)
    migrated.setdefault("video_seconds", 5)
    migrated.setdefault("video_fps", 16)

    return migrated


def load_settings() -> dict:
    ensure_directories()
    if not SETTINGS_FILE.exists():
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()

    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        data = {}

    settings = DEFAULT_SETTINGS.copy()
    settings.update(_migrate_settings(data))
    return settings


def save_settings(settings: dict) -> None:
    ensure_directories()
    SETTINGS_FILE.write_text(
        json.dumps(settings, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
