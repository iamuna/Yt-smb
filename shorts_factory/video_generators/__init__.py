"""Local/pluggable video-generation providers."""

from .base import VideoGenerationRequest, VideoGenerationResult, VideoGenerator
from .registry import available_video_generators, get_video_generator

__all__ = [
    "VideoGenerationRequest",
    "VideoGenerationResult",
    "VideoGenerator",
    "available_video_generators",
    "get_video_generator",
]
