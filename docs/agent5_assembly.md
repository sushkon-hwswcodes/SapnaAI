# Agent 5 — Final Assembly

## Role
Stitches all scene clips, audio files, and subtitles into the final video. Runs last — only starts after both Agent 3 and Agent 4 signal completion.

## Dependencies
- **Waits on:** Agent 3 (audio + subtitles.srt) AND Agent 4 (all clips)
- **Blocks nothing** — final stage

## Tools
- **FFmpeg** (all tasks)

## Tasks
1. Verify all expected files exist: `clips/scene_{n}.mp4` and `audio/scene_{n}.wav` for every scene in `scenes.json`
2. Build FFmpeg concat file listing all clips in order
3. Concatenate clips with crossfade transitions into a single silent video
4. Build combined audio track from all `scene_{n}.wav` files
5. Mux video + audio
6. Burn `subtitles.srt` onto the video
7. Encode final output to H.264 mp4
8. Write to `/workspace/output/final_story.mp4`
9. Update `/workspace/status/agent5.json` → `done`

## FFmpeg Commands

### Step 1 — Build concat list
```bash
# concat_list.txt
file 'clips/scene_1.mp4'
file 'clips/scene_2.mp4'
...
```

### Step 2 — Concatenate clips with crossfade
```bash
ffmpeg -f concat -safe 0 -i concat_list.txt \
  -vf "xfade=transition=fade:duration=0.3:offset={offset}" \
  -c:v libx264 -preset fast \
  video_only.mp4
```

### Step 3 — Concatenate audio
```bash
ffmpeg -i audio/scene_1.wav -i audio/scene_2.wav ... \
  -filter_complex "[0:a][1:a]concat=n={n}:v=0:a=1" \
  combined_audio.wav
```

### Step 4 — Mux video + audio
```bash
ffmpeg -i video_only.mp4 -i combined_audio.wav \
  -c:v copy -c:a aac -shortest \
  video_with_audio.mp4
```

### Step 5 — Burn subtitles
```bash
ffmpeg -i video_with_audio.mp4 \
  -vf "subtitles=subtitles.srt:force_style='FontSize=20,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,Outline=2'" \
  -c:a copy \
  output/final_story.mp4
```

## Optional: Background Music
If `story_config.json` includes a `background_music` path:
```bash
ffmpeg -i video_with_audio.mp4 -i background_music.mp3 \
  -filter_complex "[1:a]volume=0.15[bg];[0:a][bg]amix=inputs=2:duration=first" \
  -c:v copy output/final_story.mp4
```

## Output Encoding Settings
```
Video codec:   libx264
CRF:           18 (high quality)
Preset:        fast
Audio codec:   aac
Audio bitrate: 192k
Resolution:    1280x720 (inherits from clips)
```

## Inputs
| File | Description |
|------|-------------|
| `/workspace/clips/scene_{n}.mp4` | Animated scene clips from Agent 4 |
| `/workspace/audio/scene_{n}.wav` | Narration audio from Agent 3 |
| `/workspace/subtitles.srt` | Subtitle file from Agent 3 |
| `/workspace/scenes.json` | Scene count and ordering |

## Outputs
| File | Description |
|------|-------------|
| `/workspace/output/final_story.mp4` | Final video with audio and burned subtitles |
| `/workspace/status/agent5.json` | Status: done or error |
