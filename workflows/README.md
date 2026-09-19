# YT SMB local AI video workflow

YT SMB includes a ready-to-use local **Wan2.2 TI2V-5B** API workflow.

## Normal setup

You do **not** need to build a ComfyUI workflow manually.

Run:

`setup.bat`

When prompted:

`Install the free local VIDEO GENERATOR now? [Y/N]`

Choose **Y**.

YT SMB then:

1. Downloads the latest official NVIDIA ComfyUI Windows portable build.
2. Extracts it under `vendor/`.
3. Downloads the required Wan2.2 5B diffusion model.
4. Downloads the Wan text encoder.
5. Downloads the Wan2.2 VAE.
6. Uses the bundled `workflows/wan22_5b_t2v_api.json`.
7. Writes the workflow and local ComfyUI URL into YT SMB settings.
8. Keeps `allow_paid_services=False`.

After setup, use:

`start_video_generator.bat`

or click **GENERATE VIDEO** in YT SMB; the app can launch the local generator automatically.

## Default generation path

Prompt → local ComfyUI → Wan2.2 5B → moving WebM → FFmpeg finishing → **1080×1920 MP4**.

The raw generation target is intentionally smaller for local GPU practicality. The result handed back by YT SMB is a true 9:16 Short.

## Custom workflows

Advanced users can still choose another API-format ComfyUI workflow in Settings.

YT SMB recursively replaces these exact values:

- `__YT_SMB_PROMPT__`
- `__YT_SMB_NEGATIVE__`
- `__YT_SMB_WIDTH__`
- `__YT_SMB_HEIGHT__`
- `__YT_SMB_FRAMES__`
- `__YT_SMB_FPS__`
- `__YT_SMB_SEED__`

The generator is provider/workflow based, so a future local model can replace Wan without rewriting the app.

## Cost rule

The local generator is marked as zero-metered-cost. YT SMB does not automatically fall back to a paid video API.
