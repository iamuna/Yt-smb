from __future__ import annotations

import copy
import json
import time
from pathlib import Path
from urllib.parse import urlencode

import requests

from ..config import OUTPUT_DIR
from ..cost_policy import ServiceCostProfile, assert_service_allowed
from ..utils import safe_slug
from .base import VideoGenerationRequest, VideoGenerationResult, VideoGenerator


class ComfyUIWanGenerator(VideoGenerator):
    provider_id = "comfyui_wan22"
    display_name = "Local ComfyUI / Wan2.2"
    cost_profile = ServiceCostProfile(
        service_id="comfyui-wan22-local",
        may_charge_money=False,
        note="Runs on the user's own computer through a local ComfyUI server.",
    )

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8188",
        workflow_file: Path | None = None,
        timeout_seconds: int = 1800,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.workflow_file = workflow_file
        self.timeout_seconds = timeout_seconds

    def ready(self) -> bool:
        try:
            response = requests.get(
                f"{self.base_url}/system_stats",
                timeout=2,
            )
            return response.ok
        except requests.RequestException:
            return False

    @staticmethod
    def _replace_placeholders(value, mapping: dict[str, object]):
        if isinstance(value, dict):
            return {
                key: ComfyUIWanGenerator._replace_placeholders(item, mapping)
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [
                ComfyUIWanGenerator._replace_placeholders(item, mapping)
                for item in value
            ]
        if isinstance(value, str) and value in mapping:
            return mapping[value]
        return value

    def _load_workflow(self, request: VideoGenerationRequest) -> dict:
        workflow_file = self.workflow_file
        if workflow_file is None or not workflow_file.is_file():
            raise RuntimeError(
                "No ComfyUI API workflow is configured. Open Settings and choose "
                "an API-format Wan2.2 workflow JSON. See workflows/README.md."
            )

        try:
            raw = json.loads(workflow_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(
                f"Could not read ComfyUI workflow: {workflow_file}"
            ) from exc

        # ComfyUI API exports are usually the prompt graph itself, but allow
        # a wrapper with a top-level 'prompt' key too.
        graph = raw.get("prompt", raw)
        if not isinstance(graph, dict):
            raise RuntimeError("Configured ComfyUI workflow is not an API prompt graph.")

        mapping = {
            "__YT_SMB_PROMPT__": request.prompt,
            "__YT_SMB_NEGATIVE__": request.negative_prompt,
            "__YT_SMB_WIDTH__": int(request.width),
            "__YT_SMB_HEIGHT__": int(request.height),
            "__YT_SMB_FRAMES__": int(request.frames),
            "__YT_SMB_FPS__": int(request.fps),
            "__YT_SMB_SEED__": int(request.seed),
        }
        return self._replace_placeholders(copy.deepcopy(graph), mapping)

    def _queue_prompt(self, graph: dict) -> str:
        response = requests.post(
            f"{self.base_url}/prompt",
            json={"prompt": graph},
            timeout=30,
        )
        if not response.ok:
            raise RuntimeError(
                f"ComfyUI rejected the workflow ({response.status_code}): "
                f"{response.text[:1000]}"
            )
        prompt_id = str(response.json().get("prompt_id") or "")
        if not prompt_id:
            raise RuntimeError("ComfyUI did not return a prompt_id.")
        return prompt_id

    @staticmethod
    def _find_media(history_item: dict) -> dict | None:
        outputs = history_item.get("outputs") or {}
        preferred_keys = ("videos", "gifs", "images")
        for output in outputs.values():
            if not isinstance(output, dict):
                continue
            for key in preferred_keys:
                items = output.get(key) or []
                for item in items:
                    if isinstance(item, dict) and item.get("filename"):
                        return item
        return None

    def _wait_for_media(self, prompt_id: str) -> dict:
        deadline = time.time() + self.timeout_seconds
        while time.time() < deadline:
            response = requests.get(
                f"{self.base_url}/history/{prompt_id}",
                timeout=20,
            )
            if response.ok:
                payload = response.json()
                item = payload.get(prompt_id)
                if isinstance(item, dict):
                    status = item.get("status") or {}
                    if status.get("status_str") == "error":
                        raise RuntimeError(
                            f"ComfyUI generation failed: {json.dumps(status)[:1200]}"
                        )
                    media = self._find_media(item)
                    if media:
                        return media
            time.sleep(1.5)

        raise RuntimeError(
            f"Video generation timed out after {self.timeout_seconds} seconds."
        )

    def _download_media(self, media: dict, destination: Path) -> Path:
        query = urlencode(
            {
                "filename": media["filename"],
                "subfolder": media.get("subfolder", ""),
                "type": media.get("type", "output"),
            }
        )
        response = requests.get(
            f"{self.base_url}/view?{query}",
            stream=True,
            timeout=120,
        )
        response.raise_for_status()

        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
        return destination

    def generate(
        self,
        request: VideoGenerationRequest,
        *,
        allow_paid_services: bool = False,
    ) -> VideoGenerationResult:
        assert_service_allowed(
            self.cost_profile,
            allow_paid_services=allow_paid_services,
        )
        if not request.prompt.strip():
            raise RuntimeError("Video prompt is empty.")
        if not self.ready():
            raise RuntimeError(
                "ComfyUI is not reachable at "
                f"{self.base_url}. Start local ComfyUI first."
            )

        graph = self._load_workflow(request)
        prompt_id = self._queue_prompt(graph)
        media = self._wait_for_media(prompt_id)

        source_name = str(media.get("filename") or "generated.mp4")
        suffix = Path(source_name).suffix.lower()
        if suffix not in {".mp4", ".webm", ".mov", ".gif"}:
            suffix = ".mp4"

        output_dir = request.output_dir or (OUTPUT_DIR / "generated")
        slug = safe_slug(request.prompt)[:42]
        destination = output_dir / f"{slug}-{request.seed}{suffix}"
        self._download_media(media, destination)

        return VideoGenerationResult(
            path=destination,
            provider=self.display_name,
            prompt=request.prompt,
            seed=request.seed,
            metadata={
                "prompt_id": prompt_id,
                "source_filename": source_name,
                "width": request.width,
                "height": request.height,
                "frames": request.frames,
                "fps": request.fps,
            },
        )
