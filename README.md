# YT SMB — Shorts Factory

Windows-first automation for producing YouTube Shorts from original scripts plus footage you own or are licensed to reuse.

## Current version: v0.3 free-local architecture

The normal YT SMB workflow is designed to run without a metered AI bill:

- **Local AI:** Ollama running on your PC.
- **Default model:** `qwen2.5:3b`.
- **Local narration:** Windows speech through `pyttsx3`.
- **Editing:** FFmpeg.
- **Queue/database:** SQLite.
- **Online B-roll:** replaceable provider interface; Pexels is the current provider.
- **YouTube upload:** official OAuth/Data API integration.
- **Paid-provider guard:** potentially paid providers are blocked unless the project is deliberately changed to allow them.

External services can change their pricing, quotas, or terms in the future. YT SMB is designed to stop/fail instead of silently falling back to a paid provider.

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
3. Let setup install Python packages.
4. If FFmpeg is missing, setup can install it through Windows Package Manager.
5. If Ollama is missing, setup can install it through Windows Package Manager.
6. Let setup download the free local `qwen2.5:3b` model.
7. Double-click `start.bat`.
8. Optional: open **Settings** and add a Pexels API key for online B-roll.
9. Type a topic/niche.
10. Click **AUTO MAKE SHORT**.

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
- Single Windows executable/installer.
