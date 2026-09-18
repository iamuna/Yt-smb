from __future__ import annotations

import json
from dataclasses import dataclass

from openai import OpenAI


@dataclass
class ShortPlan:
    topic: str
    hook: str
    script: str
    title: str
    description: str
    tags: list[str]
    search_terms: list[str]


def _extract_json(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].lstrip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start < 0 or end < start:
        raise RuntimeError("AI did not return a usable content plan.")
    return json.loads(cleaned[start : end + 1])


def generate_short_plan(
    topic: str,
    target_seconds: int,
    api_key: str,
    model: str = "gpt-5.6-luna",
) -> ShortPlan:
    if not api_key.strip():
        raise RuntimeError("Add your OpenAI API key in Settings first.")

    client = OpenAI(api_key=api_key.strip())
    prompt = f"""
Create one original YouTube Short about this topic/niche:

{topic.strip()}

Target duration: about {target_seconds} seconds.

Requirements:
- Strong first-second hook.
- Clear factual or entertaining payoff.
- Natural spoken narration, not corporate language.
- Do not copy wording from existing videos.
- Avoid unsupported claims.
- Provide 3 to 5 visual search terms suitable for stock B-roll.
- Produce metadata suitable for YouTube Shorts.
- Keep the title concise.
- Description may contain #Shorts.
- Return ONLY valid JSON with exactly these keys:
  hook: string
  script: string
  title: string
  description: string
  tags: array of strings
  search_terms: array of strings
""".strip()

    response = client.responses.create(
        model=model,
        input=prompt,
    )
    data = _extract_json(response.output_text)

    return ShortPlan(
        topic=topic.strip(),
        hook=str(data.get("hook", "")).strip(),
        script=str(data.get("script", "")).strip(),
        title=str(data.get("title", "")).strip(),
        description=str(data.get("description", "")).strip(),
        tags=[str(x).strip() for x in data.get("tags", []) if str(x).strip()][:15],
        search_terms=[
            str(x).strip()
            for x in data.get("search_terms", [])
            if str(x).strip()
        ][:5],
    )
