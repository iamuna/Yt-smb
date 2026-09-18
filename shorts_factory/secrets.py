from __future__ import annotations

import json
import os

from .config import DATA_DIR

SECRETS_FILE = DATA_DIR / "secrets.json"

DEFAULT_SECRETS = {
    "source_provider_keys": {
        "pexels": "",
    },
    "youtube_client_secrets": "",
}


def _migrate_secrets(data: dict) -> dict:
    migrated = dict(data)
    keys = dict(migrated.get("source_provider_keys") or {})

    legacy_pexels = str(migrated.get("pexels_api_key", "")).strip()
    if legacy_pexels and not keys.get("pexels"):
        keys["pexels"] = legacy_pexels

    if os.getenv("PEXELS_API_KEY"):
        keys["pexels"] = os.environ["PEXELS_API_KEY"]

    migrated["source_provider_keys"] = keys
    return migrated


def load_secrets() -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    data = {}
    if SECRETS_FILE.exists():
        try:
            data = json.loads(SECRETS_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}

    migrated = _migrate_secrets(data)
    merged = DEFAULT_SECRETS.copy()
    merged.update(migrated)
    merged["source_provider_keys"] = {
        **DEFAULT_SECRETS["source_provider_keys"],
        **dict(migrated.get("source_provider_keys") or {}),
    }
    return merged


def get_source_api_key(secrets: dict, provider_id: str) -> str:
    keys = dict(secrets.get("source_provider_keys") or {})
    return str(keys.get(provider_id, "")).strip()


def set_source_api_key(secrets: dict, provider_id: str, value: str) -> dict:
    updated = dict(secrets)
    keys = dict(updated.get("source_provider_keys") or {})
    keys[provider_id] = value.strip()
    updated["source_provider_keys"] = keys
    return updated


def save_secrets(values: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = DEFAULT_SECRETS.copy()
    payload.update(values)
    payload["source_provider_keys"] = dict(
        values.get("source_provider_keys") or {}
    )
    SECRETS_FILE.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
