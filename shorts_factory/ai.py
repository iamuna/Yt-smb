from __future__ import annotations

import json
from dataclasses import dataclass

import requests

from .cost_policy import ServiceCostProfile, assert_service_allowed

OLLAMA_PROFILE = ServiceCostProfile(
    service_id="ollama-local",
    may_charge_money=False,
    note="Runs on the user's own PC. No per-token/API billing.",
)


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
        raise RuntimeError("Local AI did not return a usable content plan.")
    return json.loads(cleaned[start : end + 1])


def ollama_ready(base_url: str = "http://127.0.0.1:11434") -> bool:
    try:
        response = requests.get(f"{base_url.rstrip('/')}/api/tags", timeout=2)
        return response.ok
    except requests.RequestException:
        return False


def generate_short_plan(
    topic: str,
    target_seconds: int,
    model: str = "qwen2.5:3b",
    *,
    base_url: str = "http://127.0.0.1:11434",
    allow_paid_services: bool = False,
) -> ShortPlan:
    # This guard is intentionally here even though Ollama is free/local.
    # Future AI providers must define their own cost profile and pass the same gate.
    assert_service_allowed(
        OLLAMA_PROFILE,
        allow_paid_services=allow_paid_services,
    )

    if not topic.strip():
        raise RuntimeError("Type a topic or niche first.")

    prompt = f"""
Create one original YouTube Short about this topic/niche:

{topic.strip()}

Target duration: about {target_seconds} seconds.

Requirements:
- Strong first-second hook.
- Clear factual or entertaining payoff.
- Natural spoken narration.
- Do not copy wording from existing videos.
- Avoid unsupported claims.
- Provide 3 to 5 visual search terms suitable for licensed stock B-roll.
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

    try:
        response = requests.post(
            f"{base_url.rstrip('/')}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0.7,
                },
            },
            timeout=240,
        )
    except requests.RequestException as exc:
        raise RuntimeError(
            "Local AI is not reachable. Install/start Ollama, then run "
            f"'ollama pull {model}'. No paid API key is required."
        ) from exc

    if response.status_code == 404:
        raise RuntimeError(
            f"Ollama is running, but model '{model}' is unavailable. "
            f"Run: ollama pull {model}"
        )
    if not response.ok:
        raise RuntimeError(
            f"Local AI request failed ({response.status_code}): "
            f"{response.text[:500]}"
        )

    payload = response.json()
    data = _extract_json(str(payload.get("response", "")))

    hook = str(data.get("hook", "")).strip()
    script = str(data.get("script", "")).strip()
    if not hook or not script:
        raise RuntimeError("Local AI returned an incomplete Short plan.")

    return ShortPlan(
        topic=topic.strip(),
        hook=hook,
        script=script,
        title=str(data.get("title", "")).strip() or hook,
        description=str(data.get("description", "")).strip() or "#Shorts",
        tags=[str(x).strip() for x in data.get("tags", []) if str(x).strip()][:15],
        search_terms=[
            str(x).strip()
            for x in data.get("search_terms", [])
            if str(x).strip()
        ][:5],
    )
