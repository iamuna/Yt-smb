# YT SMB local AI video workflow

YT SMB can generate video through a **local ComfyUI server**.

The default provider is designed for **Wan2.2 TI2V-5B** or another local ComfyUI video workflow.

## One-time setup

1. Install and start ComfyUI locally.
2. Install/download the video model used by your workflow.
3. Build or load a working text-to-video workflow in ComfyUI.
4. Export the workflow in **API format**.
5. Replace the relevant values in the exported JSON with YT SMB placeholders below.
6. Save the JSON somewhere on your computer.
7. In YT SMB, open **Settings → Wan / ComfyUI workflow → Browse** and select it.

## Placeholders

YT SMB recursively replaces these exact string values before sending the workflow to ComfyUI:

- `__YT_SMB_PROMPT__`
- `__YT_SMB_NEGATIVE__`
- `__YT_SMB_WIDTH__`
- `__YT_SMB_HEIGHT__`
- `__YT_SMB_FRAMES__`
- `__YT_SMB_FPS__`
- `__YT_SMB_SEED__`

Example: if your positive text encoder node contains:

```json
{
  "inputs": {
    "text": "__YT_SMB_PROMPT__"
  }
}
```

YT SMB replaces that value with the prompt typed in the app.

For width/height/frame count/seed inputs, replace the normal numeric value with the corresponding placeholder string. YT SMB substitutes the correct integer before queueing the workflow.

## Output requirement

The workflow must save or expose a generated media output in the ComfyUI history response.

The current adapter looks for output entries named:

- `videos`
- `gifs`
- `images`

Video output is preferred.

## Shorts format

The local generation target defaults to **480×832**, close to 9:16 and much cheaper to generate than native 1080×1920.

The finishing pipeline can upscale/crop the result to **1080×1920** for YouTube Shorts.

## Cost rule

The local ComfyUI/Wan provider is marked as a zero-metered-cost provider.

YT SMB will not automatically switch to a paid video-generation API if local generation fails.
