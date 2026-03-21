# Agent 3 — Audio + Subtitles

## Role
Generates narration audio for each scene and produces a word-level SRT subtitle file for the full video.

## Dependencies
- **Waits on:** Agent 1 (`scenes.json` must exist)
- **Runs in parallel with:** Agent 2
- **Unblocks:** Agent 5 (needs audio files and subtitles.srt)

## Models
- **TTS:** Coqui XTTS v2 (voice cloning, multiple characters) or Kokoro TTS (fast, simpler setup)
- **Alignment:** WhisperX (word-level forced alignment for precise subtitle timing)

## Tasks
1. Read `/workspace/scenes.json`
2. For each scene:
   a. Select voice based on `characters[0]` (map character name → voice ID or cloned voice)
   b. Run TTS on `narration` text
   c. Save to `/workspace/audio/scene_{n}.wav`
3. Run WhisperX alignment on each audio file to get word-level timestamps
4. Build `subtitles.srt` with cumulative time offsets across all scenes
5. Write `/workspace/subtitles.srt`
6. Update `/workspace/status/agent3.json` → `done`

## Voice Mapping
Define in `story_config.json` or default to narrator voice:
```json
{
  "voices": {
    "narrator": "voices/narrator.wav",
    "Elena": "voices/elena.wav",
    "default": "voices/narrator.wav"
  }
}
```
If using Coqui XTTS v2, voice cloning requires a 3–10 second reference audio clip per character.
If using Kokoro TTS, map character names to built-in voice IDs.

## SRT Generation Logic
1. Compute cumulative start time for each scene: `sum of duration_seconds for all previous scenes`
2. For each word in WhisperX output, offset its timestamp by the scene start time
3. Group words into subtitle lines of 6–8 words max
4. Format as standard SRT:

```
1
00:00:00,000 --> 00:00:02,400
In a quiet mountain village,

2
00:00:02,400 --> 00:00:05,100
a young girl discovers a strange map.
```

## Audio Settings
```python
{
  "sample_rate": 22050,
  "language": "en",
  "speed": 1.0
}
```

## Inputs
| File | Description |
|------|-------------|
| `/workspace/scenes.json` | Scene list with narration text |
| `voices/{character}.wav` | Reference audio clips for voice cloning |

## Outputs
| File | Description |
|------|-------------|
| `/workspace/audio/scene_{n}.wav` | Narration audio per scene |
| `/workspace/subtitles.srt` | Full word-level subtitle file |
| `/workspace/status/agent3.json` | Status with per-scene progress |
