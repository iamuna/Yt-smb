# Changelog

## v0.3 — Free-local architecture

- Replaced mandatory OpenAI API script generation with local Ollama.
- Default local model is `qwen2.5:3b`.
- Replaced Edge TTS with local Windows speech using `pyttsx3`.
- Removed OpenAI and Edge TTS packages from default requirements.
- Added `cost_policy.py` to prevent accidental paid-provider use.
- Reworked B-roll acquisition into a provider plugin architecture.
- Moved Pexels into `shorts_factory/providers/pexels.py`.
- Added a provider registry so Pexels can be replaced later without rewriting editing/orchestration.
- Generalized provider API-key storage.
- Added migration from v0.2 settings.
- Updated the GUI for local AI and generic online B-roll.
- Updated Windows setup to install/detect Ollama and pull the local model.
- Added `AGENTS.md` and provider documentation for future developers/AIs.

## v0.2 — Automation core

- AI plan generation.
- Pexels B-roll.
- Timed captions.
- Upload queue.
- YouTube OAuth/upload.
- One-click Auto Make workflow.

## v0.1 — Initial MVP

- Windows GUI.
- Local clips.
- FFmpeg vertical rendering.
- Basic narration/render pipeline.
