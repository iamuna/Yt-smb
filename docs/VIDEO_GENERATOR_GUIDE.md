# Video generator architecture

YT SMB separates **video generation** from **B-roll sourcing**.

B-roll providers live under:

`shorts_factory/providers/`

Video generators live under:

`shorts_factory/video_generators/`

This distinction is intentional. A video generator creates new moving footage from a prompt; a source provider downloads permitted existing media.

## Current generator

`comfyui_wan22`

Implementation:

`shorts_factory/video_generators/comfyui_wan.py`

The adapter talks to a local ComfyUI server and submits an API-format workflow JSON.

The current recommended local model family is Wan2.2, with TI2V-5B as the practical starting point.

## Adding another generator later

Implement the `VideoGenerator` interface from:

`shorts_factory/video_generators/base.py`

Required properties:

- `provider_id`
- `display_name`
- `cost_profile`

Required methods:

- `ready()`
- `generate()`

Then register the provider in:

`shorts_factory/video_generators/registry.py`

Do not hard-code generator-specific behavior into the editor or GUI.

## Cost safety

Every generator declares a `ServiceCostProfile`.

A cloud/provider API that can incur charges must use:

```python
may_charge_money=True
```

The current UI passes `allow_paid_services=False`, so such a provider will be blocked unless the project later adds an explicit opt-in flow.

## Output contract

A generator returns `VideoGenerationResult` containing:

- local output path
- provider name
- prompt
- seed
- metadata

The rest of YT SMB should only depend on this result, not on ComfyUI-specific internals.

## Current UI behavior

The top prompt/topic field is also the raw video-generation prompt.

**GENERATE VIDEO**:

1. Reads the prompt.
2. Uses the configured local generator.
3. Generates a short moving clip.
4. Saves it under `output/generated/`.
5. Makes it available as source material for the Shorts pipeline.

Future work should add a direct “generate visuals for AUTO MAKE SHORT” mode so generated scenes can be created per narration segment automatically.
