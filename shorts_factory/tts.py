from __future__ import annotations

from pathlib import Path

import pyttsx3

from .cost_policy import ServiceCostProfile, assert_service_allowed

LOCAL_TTS_PROFILE = ServiceCostProfile(
    service_id="windows-local-tts",
    may_charge_money=False,
    note="Uses speech synthesis installed on the local Windows machine.",
)


def available_voices() -> list[tuple[str, str]]:
    engine = pyttsx3.init()
    try:
        return [
            (str(getattr(voice, "id", "")), str(getattr(voice, "name", "Voice")))
            for voice in engine.getProperty("voices")
        ]
    finally:
        engine.stop()


def synthesize_voice(
    text: str,
    voice: str,
    output_path: Path,
    *,
    allow_paid_services: bool = False,
) -> Path:
    assert_service_allowed(
        LOCAL_TTS_PROFILE,
        allow_paid_services=allow_paid_services,
    )
    if not text.strip():
        raise RuntimeError("Narration text is empty.")

    output_path = output_path.with_suffix(".wav")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    engine = pyttsx3.init()
    try:
        if voice and voice != "default":
            voice_ids = {
                str(getattr(item, "id", "")): item
                for item in engine.getProperty("voices")
            }
            if voice in voice_ids:
                engine.setProperty("voice", voice)

        engine.setProperty("rate", 185)
        engine.setProperty("volume", 1.0)
        engine.save_to_file(text.strip(), str(output_path))
        engine.runAndWait()
    finally:
        engine.stop()

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError(
            "Local text-to-speech did not create audio. "
            "Check that Windows speech voices are installed."
        )
    return output_path
