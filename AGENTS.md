# AGENTS.md — YT SMB developer/AI handoff

This file is the first thing a new developer or coding AI should read before changing the project.

## Product goal

YT SMB is a Windows-first YouTube Shorts automation app. The intended end state is:

topic/niche -> idea -> script -> permitted visual sources -> edit -> local narration -> captions -> quality checks -> queue -> YouTube -> analytics feedback

The UI should remain simple enough that the normal user flow is one primary **AUTO MAKE SHORT** button.

## Non-negotiable cost rule

**The default YT SMB workflow must not create metered AI/API charges.**

Current free/local defaults:

- Content AI: local Ollama.
- Default model: `qwen2.5:3b`.
- Narration: local Windows speech through `pyttsx3`.
- Editing: local FFmpeg.
- Queue/database: local SQLite.
- AI video generation: provider interface backed by local ComfyUI; default provider id is `comfyui_local_video`.
- B-roll: provider interface; Pexels is currently registered and treated as a free provider.
- YouTube: official OAuth/Data API integration; auto-upload remains off by default.

`shorts_factory/cost_policy.py` exists specifically to stop accidental paid-service fallback.

`settings["allow_paid_services"]` defaults to `False`. Do not silently change it to `True`. If paid providers are ever added, they must declare `may_charge_money=True` and must be blocked unless the user deliberately opts in.

Never implement "free provider failed, so automatically use a paid API" behavior.

External services can change their pricing or terms in the future. If a service that is currently considered free changes, the correct failure mode is to stop that feature and tell the user, not incur a charge.

## Current architecture

### AI

`shorts_factory/ai.py`

- Calls a local Ollama server at `http://127.0.0.1:11434` by default.
- Produces `ShortPlan`: hook, narration, title, description, tags and visual search terms.
- No OpenAI API dependency is required in the default install.

### TTS

`shorts_factory/tts.py`

- Uses `pyttsx3` / local Windows voices.
- Writes WAV narration locally.
- No cloud TTS service is required.

### Source providers

All online B-roll access goes through:

- `shorts_factory/providers/base.py`
- `shorts_factory/providers/registry.py`
- `shorts_factory/sources.py`

Current provider:

- `shorts_factory/providers/pexels.py`

**Do not put Pexels-specific logic back into the editor, GUI or automation pipeline.**

To replace Pexels or add another provider, implement `SourceProvider` and register it. The GUI reads the registry dynamically.

See `docs/SOURCE_PROVIDER_GUIDE.md`.

### Video generators

Video generation is separate from B-roll sourcing.

Files:

- `shorts_factory/video_generators/base.py`
- `shorts_factory/video_generators/registry.py`
- `shorts_factory/video_generators/comfyui_wan.py`
- `shorts_factory/video_generation.py`

The default provider talks to a local ComfyUI server and injects prompt/size/frame/seed values into an API-format workflow JSON.

The current adapter is intentionally workflow-agnostic: Wan2.2, Kandinsky 5.0 T2V Lite, or another compatible local ComfyUI workflow can be used.

Never hard-code the rest of YT SMB to one video model. See `docs/VIDEO_GENERATOR_GUIDE.md`.

### Rendering

`shorts_factory/editor.py`

- Normalizes mixed source videos.
- Creates vertical 1080x1920 output.
- Adds a hook overlay.
- Adds timed burned-in caption cards.
- Uses FFmpeg locally.

### Orchestration

`shorts_factory/automation.py`

Provider-neutral one-click path.

### Upload queue

`shorts_factory/queue.py`

Local SQLite queue.

### YouTube

`shorts_factory/youtube.py`

Official OAuth upload flow. Auto-upload is OFF by default and upload privacy defaults to private.

## Safety/content rule

Do not build an unauthorized YouTube/TikTok downloader/reposter. Source footage should be user-owned, licensed, public-domain, or supplied by a provider whose terms allow the intended use.

The application can transform permitted source media, but it should not be designed to evade copyright systems or remove ownership markers.

## v0.3 migration notes

Earlier v0.2 code used:

- OpenAI API for script generation.
- Edge TTS.
- Pexels calls directly in `sources.py`.
- Settings named `use_pexels`.

v0.3 changed this to:

- Ollama local AI.
- Windows local TTS.
- Generic source-provider interface.
- `use_online_sources` + `source_provider`.
- A cost-policy guard.
- Automatic migration of old settings/secrets where practical.

Do not reintroduce OpenAI as a mandatory dependency.

## Setup assumptions

Windows user runs:

1. `setup.bat`
2. Installs/detects Python dependencies.
3. Installs/detects FFmpeg.
4. Installs/detects Ollama.
5. Pulls `qwen2.5:3b`.
6. Runs `start.bat`.

Pexels remains optional. Local source clips work without a Pexels key.

## Immediate next engineering priorities

1. Full runtime smoke test on a real Windows machine.
2. Better local voice selection in Settings.
3. Clip-to-sentence semantic matching instead of round-robin clips.
4. Audio/music mixing with safe loudness.
5. Pre-upload quality-control gate.
6. Background BOT MODE with a user-controlled posting schedule.
7. Analytics ingestion and performance learning.
8. Integrate generated scenes directly into AUTO MAKE SHORT.
9. Package as a signed/portable Windows executable when stable.

## Development discipline

- Keep the main UI simple.
- Preserve backwards-compatible settings migration where reasonable.
- Run the GitHub validation workflow after changes.
- Prefer provider interfaces over hard-coded vendor logic.
- Record major architecture changes in this file and README.
- Never commit API keys, OAuth secrets, generated media or user data.
