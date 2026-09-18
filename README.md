# YT SMB — Shorts Factory

Windows-first automation for producing YouTube Shorts from original scripts plus footage you own or are licensed to reuse.

## Current version: v0.2 automation core

The app now supports:

- One-button **AUTO MAKE SHORT** workflow.
- AI idea selection, hook, script, title, description, tags, and B-roll search terms.
- Local source clips.
- Optional Pexels stock-video search/download for permitted B-roll.
- 9:16 automatic editing with FFmpeg.
- AI voice-over.
- Burned-in timed captions.
- Local SQLite upload queue.
- Google OAuth connection for YouTube.
- Manual **UPLOAD NEXT** action.
- Optional automatic upload after each successful Auto Short.
- Private / unlisted / public privacy selection.
- Automatic Python syntax validation through GitHub Actions.

This project does not download and repost copyrighted YouTube/TikTok videos without permission.

## Fastest Windows setup

1. Download/clone this repository.
2. Double-click `setup.bat`.
3. If FFmpeg is missing and Windows Package Manager is available, setup can install it for you.
4. Double-click `start.bat`.
5. Open **Settings** in the app.
6. Add your OpenAI API key.
7. Optional: add a Pexels API key for automatic stock B-roll.
8. Optional: choose your Google OAuth client-secrets JSON to enable YouTube upload.
9. Type a topic or niche.
10. Click **AUTO MAKE SHORT**.

## What AUTO MAKE SHORT does

```
topic / niche
    ↓
AI picks a specific Short idea
    ↓
hook + narration + title + description + tags
    ↓
visual search terms
    ↓
local clips + optional Pexels B-roll
    ↓
voice-over
    ↓
9:16 edit + timed burned-in captions
    ↓
MP4 output
    ↓
upload queue
    ↓
optional YouTube upload
```

## YouTube publishing safety

Automatic upload is **OFF by default**.

When enabled in Settings, the app uploads completed Auto Shorts using the privacy level you select. Start with `private` while testing.

YouTube uses OAuth 2.0. Create a Google Cloud project, enable the YouTube Data API v3, create an OAuth desktop client, download its client-secrets JSON, then select that JSON in YT SMB Settings.

Some newer/unverified YouTube API projects can be restricted to private uploads until the project completes YouTube's audit process.

## Pexels source mode

Pexels mode is optional. When enabled and an API key is configured, YT SMB searches the Pexels video API for portrait B-roll matching the AI-generated visual terms.

Pexels currently permits its photos/videos to be used and modified for YouTube under the Pexels license. Depicted brands, people, trademarks, and other third-party rights can still require care.

The UI identifies Pexels as the source provider when the integration is used.

## Local files and secrets

The following are intentionally ignored by Git:

- `data/` — settings, API secrets, OAuth token, queue database
- `input/`
- `output/`
- `temp/`
- media files
- OAuth/client-secret files

Do not commit API keys or Google OAuth secrets.

## Current project structure

```
Yt-smb/
├─ app.py
├─ setup.bat
├─ start.bat
├─ requirements.txt
├─ shorts_factory/
│  ├─ ai.py
│  ├─ automation.py
│  ├─ config.py
│  ├─ editor.py
│  ├─ pipeline.py
│  ├─ queue.py
│  ├─ secrets.py
│  ├─ sources.py
│  ├─ tts.py
│  ├─ utils.py
│  └─ youtube.py
└─ .github/workflows/validate.yml
```

## Next engineering targets

- Background bot mode with posting schedule and rate limits.
- Source scoring and smarter clip-to-sentence matching.
- Better caption animation and emphasis.
- Music/SFX mixing and loudness normalization.
- Quality-control scoring before upload.
- YouTube statistics ingestion.
- Performance history by hook/topic/editing style.
- Feedback loop that changes future content choices based on performance.
- Packaging into a single Windows executable/installer.
