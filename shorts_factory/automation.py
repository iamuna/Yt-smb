from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .ai import ShortPlan, generate_short_plan
from .config import TEMP_DIR
from .pipeline import BuildRequest, BuildResult, create_short
from .queue import enqueue
from .secrets import load_secrets
from .sources import SourceAsset, fetch_pexels_broll


@dataclass
class AutoRequest:
    topic: str
    source_folder: Path
    target_seconds: int
    voice: str
    use_voice: bool
    use_pexels: bool
    auto_queue: bool
    privacy_status: str
    ai_model: str


@dataclass
class AutoResult:
    plan: ShortPlan
    build: BuildResult
    sources: list[SourceAsset]
    queue_id: int | None


def run_auto_short(request: AutoRequest) -> AutoResult:
    secrets = load_secrets()

    plan = generate_short_plan(
        topic=request.topic,
        target_seconds=request.target_seconds,
        api_key=secrets["openai_api_key"],
        model=request.ai_model,
    )

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    assets: list[SourceAsset] = []

    if request.use_pexels and secrets.get("pexels_api_key", "").strip():
        assets = fetch_pexels_broll(
            search_terms=plan.search_terms,
            api_key=secrets["pexels_api_key"],
            destination=TEMP_DIR / "pexels" / stamp,
            max_clips=6,
        )

    build = create_short(
        BuildRequest(
            source_folder=request.source_folder,
            hook=plan.hook,
            script=plan.script,
            voice=request.voice,
            target_seconds=request.target_seconds,
            use_voice=request.use_voice,
            extra_clips=[asset.path for asset in assets],
            captions=True,
        )
    )

    queue_id = None
    if request.auto_queue:
        queue_id = enqueue(
            video_path=build.output_path,
            title=plan.title or plan.hook,
            description=plan.description,
            tags=plan.tags,
            privacy_status=request.privacy_status,
        )

    return AutoResult(
        plan=plan,
        build=build,
        sources=assets,
        queue_id=queue_id,
    )
