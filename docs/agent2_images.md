# Agent 2 — Image Generation

## Role
Renders one image per scene using the scene's `image_prompt`. Applies character consistency adapter to maintain visual coherence across all scenes.

## Dependencies
- **Waits on:** Agent 1 (`scenes.json` must exist)
- **Unblocks:** Agent 4 (starts processing images as they appear)

## Models
- **Primary image gen:** FLUX.1 dev (best quality) or SDXL (lower VRAM)
- **Character consistency:** IP-Adapter (zero-shot, no training) or LoRA fine-tune (better quality, requires training)
- **Orchestration:** ComfyUI API or diffusers Python library

## Tasks
1. Read `/workspace/scenes.json`
2. Load character consistency adapter (IP-Adapter reference image or trained LoRA weights)
3. For each scene in order:
   a. Augment `image_prompt` with character consistency tokens / reference
   b. Run image generation (FLUX or SDXL)
   c. Save output immediately to `/workspace/images/scene_{n}.png`
   d. Update `progress` in status file after each scene
4. Update `/workspace/status/agent2.json` → `done` when all scenes complete

## Character Consistency Strategy

### Option A — IP-Adapter (no training needed)
- Provide one reference image per character
- Inject reference into every generation via IP-Adapter
- Works out of the box; moderate consistency

### Option B — LoRA fine-tune (recommended for best results)
- Train a LoRA on 5–20 reference images per character
- Load LoRA weights before generation loop
- Add character trigger token to every `image_prompt`
- Best consistency, requires upfront training (~30 min per character on a 24GB GPU)

## Image Generation Settings
```python
{
  "width": 1280,
  "height": 720,        # 16:9 for video
  "num_inference_steps": 28,
  "guidance_scale": 3.5,
  "seed": 42            # fixed seed per scene for reproducibility
}
```

## Prompt Augmentation
Append to every `image_prompt` before generation:
```
..., cinematic composition, 16:9, high detail, consistent character design
```

## Inputs
| File | Description |
|------|-------------|
| `/workspace/scenes.json` | Scene list with image prompts |
| `characters/ref_{name}.png` | Reference images for IP-Adapter |
| `characters/{name}.safetensors` | LoRA weights (if using Option B) |

## Outputs
| File | Description |
|------|-------------|
| `/workspace/images/scene_{n}.png` | One 1280×720 image per scene |
| `/workspace/status/agent2.json` | Status with per-scene progress |
