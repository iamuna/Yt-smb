# YT SMB — Shorts Factory

A simple Windows-first YouTube Shorts production app.

## First checkpoint

This MVP can:

- Launch with a double-click on Windows.
- Use **your own / licensed / public-domain** local video clips as source media.
- Turn those clips into a 9:16 Short using FFmpeg.
- Add a hook/title overlay.
- Optionally generate narration with Edge TTS.
- Save every finished video into an `output` folder.
- Keep YouTube publishing **OFF by default** until credentials are configured.
- Store settings locally in `data/settings.json`.

The project intentionally does **not** download or repost copyrighted YouTube/TikTok videos without permission.

## Easiest setup on Windows

1. Install Python 3.11+.
2. Install FFmpeg and make sure `ffmpeg.exe` and `ffprobe.exe` are on PATH.
3. Double-click `setup.bat`.
4. Double-click `start.bat`.
5. In the app, choose a folder containing MP4/MOV/MKV/WebM clips.
6. Enter a hook and script, then click **CREATE SHORT**.

## Roadmap

- One-click AI script generation
- Auto B-roll selection
- Animated captions
- Music/SFX mixing
- Automatic quality checks
- Queue + scheduling
- YouTube OAuth + upload
- Analytics feedback loop
- Licensed/public-domain source integrations
- Fully automatic channel mode with an approval switch
