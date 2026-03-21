# Agent 1 — Story Generation

## Role
Generates the structured scene-by-scene story JSON that feeds every other agent in the pipeline.

## Dependencies
- **Waits on:** nothing — runs first
- **Blocks:** Agents 2, 3, 4 (all depend on `scenes.json`)

## Model
- **Primary:** Mistral Nemo 12B via Ollama (fast, fits single 12–16GB GPU)
- **Higher quality:** Llama 3.1 70B via vLLM (requires ~40GB VRAM or quantised)
- **Endpoint:** `http://localhost:11434/api/generate` (Ollama) or `http://localhost:8000/v1` (vLLM)

## Tasks
1. Read `story_config.json` from `/workspace/`
2. Build a structured prompt instructing the LLM to output JSON only (no preamble, no markdown fences)
3. Call the LLM endpoint
4. Validate the response — every scene must contain all required fields
5. Retry up to 3 times if validation fails (with stricter prompt on retry)
6. Write validated output to `/workspace/scenes.json`
7. Update `/workspace/status/agent1.json` → `done`

## Prompt Template
```
You are a screenwriter. Output ONLY a valid JSON array. No explanation, no markdown.

Story config:
- Genre: {genre}
- Characters: {characters}
- Tone: {tone}
- Target duration: {duration_minutes} minutes
- Approximate scenes: {scene_count}

Each scene must have these exact fields:
{
  "scene_number": 1,
  "narration": "The narration text read aloud for this scene.",
  "image_prompt": "A detailed visual description for image generation. Include style, lighting, characters present.",
  "duration_seconds": 8,
  "characters": ["Character A"]
}

Return a JSON array of {scene_count} scenes.
```

## Output Schema (`scenes.json`)
```json
[
  {
    "scene_number": 1,
    "narration": "In a quiet mountain village, a young girl discovers a strange map...",
    "image_prompt": "A young girl with auburn hair holding an old parchment map, cobblestone street, warm golden hour light, cinematic, detailed",
    "duration_seconds": 8,
    "characters": ["Elena"]
  }
]
```

## Validation Rules
- Array must be non-empty
- Every scene must have: `scene_number`, `narration`, `image_prompt`, `duration_seconds`, `characters`
- `duration_seconds` must be a positive integer
- `characters` must be a non-empty array
- Total duration should be within 20% of target

## Inputs
| File | Description |
|------|-------------|
| `/workspace/story_config.json` | Genre, characters, tone, target duration |

## Outputs
| File | Description |
|------|-------------|
| `/workspace/scenes.json` | Validated scene array |
| `/workspace/status/agent1.json` | Status: done or error |
