# YT SMB — Shorts Factory

Windows-first automation for producing YouTube Shorts from original scripts plus footage you own or are licensed to reuse.

## Current version: v0.4 local video generator

The normal YT SMB workflow is designed to run without a metered AI bill:

- **Local AI:** Ollama running on your PC.
- **Default model:** `qwen2.5:3b`.
- **Local narration:** Windows speech through `pyttsx3`.
- **Editing:** FFmpeg.
- **Queue/database:** SQLite.
- **AI video generator:** local ComfyUI provider; supports replaceable local video workflows.
- **Online B-roll:** replaceable provider interface; Pexels is the current provider.
- **YouTube upload:** official OAuth/Data API integration.
- **Paid-provider guard:** potentially paid providers are blocked unless the project is deliberately changed to allow them.

External services can change their pricing, quotas, or terms in the future. YT SMB is designed to stop/fail instead of silently falling back to a paid provider.

## Generate video from a prompt

The main screen now has **GENERATE VIDEO**.

Type a prompt such as:

```
grainy CCTV footage of a car losing control in a rainy underground parking garage,
fixed security camera, realistic headlights, wet floor reflections, continuous motion
```

YT SMB sends the configured local ComfyUI workflow the prompt, negative prompt, seed, width, height, FPS and frame count, then saves the generated moving clip under `output/generated/`.

The default generation target is 480×832 and is intended to be finished/upscaled to 1080×1920 for Shorts.

The adapter is workflow-based, so it can use Wan2.2, Kandinsky 5.0 T2V Lite, or another compatible local ComfyUI video workflow without rewriting the app.

The bundled Wan2.2 API workflow is selected automatically; you do not need to build a ComfyUI graph by hand.

See `workflows/README.md` and `docs/VIDEO_GENERATOR_GUIDE.md` if you want to swap models/workflows later.

## What AUTO MAKE SHORT does

```
topic / niche
    ↓
local Ollama AI
    ↓
hook + narration + title + description + tags
    ↓
visual search terms
    ↓
local clips + optional configured B-roll provider
    ↓
local Windows voice-over
    ↓
9:16 FFmpeg edit + timed burned-in captions
    ↓
MP4 output
    ↓
local upload queue
    ↓
optional YouTube upload
```

## Fastest Windows setup

1. Download or clone this repository.
2. Double-click `setup.bat`.
3. Let setup install the normal YT SMB dependencies, FFmpeg, and Ollama.
4. When asked, choose **Y** to install the free local video generator.
5. The installer downloads official ComfyUI portable plus the Wan2.2 5B files and configures YT SMB automatically.
6. Double-click `start_video_generator.bat` when you want local video generation. Clicking **GENERATE VIDEO** can also start it automatically.
7. Double-click `start.bat` to launch YT SMB.
8. Type a video prompt and click **GENERATE VIDEO**, or use **AUTO MAKE SHORT** for the existing Shorts workflow.
9. Generated video is automatically finished to true **1080×1920 (9:16)** MP4.
10. Optional: add a Pexels API key or YouTube OAuth later.

No OpenAI API key is required for the default workflow.

## Source providers are replaceable

Pexels is **not** hard-coded into the editing pipeline anymore.

Online media access is isolated under:

```
shorts_factory/providers/
├─ base.py
├─ pexels.py
└─ registry.py
```

The app reads the provider registry dynamically. A future developer can add another service by implementing the `SourceProvider` interface and registering it.

See [docs/SOURCE_PROVIDER_GUIDE.md](docs/SOURCE_PROVIDER_GUIDE.md).

## Zero-paid-services rule

The architectural rule is documented in `AGENTS.md`.

`shorts_factory/cost_policy.py` blocks services marked as potentially paid when `allow_paid_services=False`, which is the default and is forced by the current UI.

A future developer should **not**:

- automatically fall back to a paid AI API,
- automatically switch to a paid stock provider,
- silently turn on paid services,
- make a paid service mandatory for normal Short creation.

If a paid provider is ever added as an optional feature, it must require an intentional user opt-in.

## YouTube publishing

Automatic upload is **OFF by default** and privacy defaults to **private**.

To enable upload:

1. Create a Google Cloud project.
2. Enable YouTube Data API v3.
3. Create an OAuth desktop client.
4. Download the client-secrets JSON.
5. Select it in YT SMB **Settings**.

The project uses the official YouTube upload API rather than browser automation.

## Pexels

Pexels is the current optional online B-roll provider.

Its API key is stored locally, not committed to Git. The provider module also keeps source/creator provenance with downloaded assets.

Provider licensing/terms should be rechecked over time because third-party policies can change.

## Files that stay local

Git ignores:

- `data/` — settings, provider keys, OAuth token, queue database
- `input/`
- `output/`
- `temp/`
- generated media
- OAuth/client-secret files

Never commit secrets or user-generated media.

## Project map

```
Yt-smb/
├─ AGENTS.md
├─ CHANGELOG.md
├─ README.md
├─ app.py
├─ setup.bat
├─ start.bat
├─ requirements.txt
├─ docs/
│  └─ SOURCE_PROVIDER_GUIDE.md
├─ shorts_factory/
│  ├─ ai.py
│  ├─ automation.py
│  ├─ config.py
│  ├─ cost_policy.py
│  ├─ editor.py
│  ├─ pipeline.py
│  ├─ providers/
│  │  ├─ base.py
│  │  ├─ pexels.py
│  │  └─ registry.py
│  ├─ queue.py
│  ├─ secrets.py
│  ├─ sources.py
│  ├─ tts.py
│  ├─ utils.py
│  └─ youtube.py
└─ .github/workflows/validate.yml
```

## For the next developer / AI

**Read `AGENTS.md` before changing the project.**

It records the product goal, zero-cost constraint, current architecture, migration history, provider rules, copyright/source rules, and next priorities.

## Next engineering targets

- Real Windows runtime smoke test and fixes from playtesting.
- Local voice selection.
- Smarter clip-to-sentence matching.
- Music/SFX and loudness normalization.
- Pre-upload quality-control gate.
- User-controlled scheduled BOT MODE.
- YouTube analytics ingestion.
- Performance feedback loop.
- Direct generated-visuals mode inside AUTO MAKE SHORT.
- Single Windows executable/installer.
