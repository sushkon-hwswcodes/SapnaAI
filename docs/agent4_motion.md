# Agent 4 — Motion + Video Clips

## Role
Animates each scene image into a short video clip. Starts processing as soon as Agent 2 writes its first image — does not wait for all images to be ready.

## Dependencies
- **Waits on:** First image from Agent 2 (file watcher trigger)
- **Also reads:** `scenes.json` for per-scene duration
- **Unblocks:** Agent 5

## Models
- **Image-to-video:** Wan2.1 (recommended, best open source i2v as of 2025) or AnimateDiff (reuses SDXL LoRAs for better character consistency)
- **Trimming:** FFmpeg

## Tasks
1. Read `/workspace/scenes.json` (for duration_seconds per scene)
2. Start file watcher on `/workspace/images/`
3. On each new `scene_{n}.png`:
   a. Run image-to-video model to generate a 2–4s motion clip
   b. Read `duration_seconds` for this scene from scenes.json
   c. Trim or freeze-pad clip to exactly match `duration_seconds`
   d. Save to `/workspace/clips/scene_{n}.mp4`
   e. Update progress in status file
4. Update `/workspace/status/agent4.json` → `done` when all scenes are processed

## File Watcher Logic
```
watch /workspace/images/ for new *.png files
on new file → extract scene number from filename → process if not already done
poll interval: 2 seconds
timeout: 30 minutes (fail if no new images for 30min)
```

## Image-to-Video Settings

### Wan2.1
```python
{
  "num_frames": 81,         # ~3 seconds at 24fps
  "guidance_scale": 5.0,
  "motion_bucket_id": 127,  # higher = more motion
  "fps": 24
}
```

### AnimateDiff (SDXL)
```python
{
  "num_frames": 16,
  "guidance_scale": 7.5,
  "motion_module": "mm_sd_v15_v2.ckpt"
}
```

## Clip Duration Matching (FFmpeg)
```bash
# If clip is longer than needed — trim
ffmpeg -i scene_{n}_raw.mp4 -t {duration_seconds} -c copy scene_{n}.mp4

# If clip is shorter than needed — freeze last frame
ffmpeg -i scene_{n}_raw.mp4 -vf "tpad=stop_mode=clone:stop_duration={pad_seconds}" scene_{n}.mp4
```

## Inputs
| File | Description |
|------|-------------|
| `/workspace/images/scene_{n}.png` | Scene images (streaming in from Agent 2) |
| `/workspace/scenes.json` | Duration per scene |

## Outputs
| File | Description |
|------|-------------|
| `/workspace/clips/scene_{n}.mp4` | Animated clip per scene, duration-matched |
| `/workspace/status/agent4.json` | Status with per-scene progress |
