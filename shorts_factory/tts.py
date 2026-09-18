from __future__ import annotations

import asyncio
from pathlib import Path

import edge_tts


async def _synthesize(text: str, voice: str, output_path: Path) -> None:
    communicate = edge_tts.Communicate(text=text, voice=voice)
    await communicate.save(str(output_path))


def synthesize_voice(text: str, voice: str, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    asyncio.run(_synthesize(text, voice, output_path))
    return output_path
