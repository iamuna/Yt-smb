from __future__ import annotations

import json
import os
from pathlib import Path

from .config import DATA_DIR

SECRETS_FILE = DATA_DIR / "secrets.json"

DEFAULT_SECRETS = {
    "openai_api_key": "",
    "pexels_api_key": "",
    "youtube_client_secrets": "",
}


def load_secrets() -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    data = {}
    if SECRETS_FILE.exists():
        try:
            data = json.loads(SECRETS_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}

    merged = DEFAULT_SECRETS.copy()
    merged.update(data)

    if os.getenv("OPENAI_API_KEY"):
        merged["openai_api_key"] = os.environ["OPENAI_API_KEY"]
    if os.getenv("PEXELS_API_KEY"):
        merged["pexels_api_key"] = os.environ["PEXELS_API_KEY"]

    return merged


def save_secrets(values: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = DEFAULT_SECRETS.copy()
    payload.update(values)
    SECRETS_FILE.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
