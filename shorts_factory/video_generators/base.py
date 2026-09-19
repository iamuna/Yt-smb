from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

from ..cost_policy import ServiceCostProfile


@dataclass
class VideoGenerationRequest:
    prompt: str
    negative_prompt: str = ""
    width: int = 480
    height: int = 832
    frames: int = 81
    fps: int = 16
    seed: int = 0
    output_dir: Path | None = None
    extra: dict = field(default_factory=dict)


@dataclass
class VideoGenerationResult:
    path: Path
    provider: str
    prompt: str
    seed: int
    metadata: dict = field(default_factory=dict)


class VideoGenerator(ABC):
    provider_id: str
    display_name: str
    cost_profile: ServiceCostProfile

    @abstractmethod
    def ready(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def generate(
        self,
        request: VideoGenerationRequest,
        *,
        allow_paid_services: bool = False,
    ) -> VideoGenerationResult:
        raise NotImplementedError
