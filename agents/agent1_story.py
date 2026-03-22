"""
Agent 1 — Story Generation
Reads story_config.json, calls an LLM to generate a structured scene array,
validates the output, and writes scenes.json.

Supported backends:
  - ollama      : local Ollama server (default)
  - vllm        : OpenAI-compatible vLLM server
  - huggingface : loads weights directly via transformers (checkpoint_path required)

See docs/agent1_story.md for full spec.
"""

import json
import logging
import re
import sys
import time
from pathlib import Path

import requests

# ── Paths ──────────────────────────────────────────────────────────────────────

WORKSPACE   = Path(__file__).parent.parent / "workspace"
MODELS_DIR  = Path(__file__).parent.parent / "models" / "story"
CONFIG_PATH = WORKSPACE / "story_config.json"
SCENES_PATH = WORKSPACE / "scenes.json"
STATUS_PATH = WORKSPACE / "status" / "agent1.json"

# ── Logging ────────────────────────────────────────────────────────────────────

logging.basicConfig(level=logging.INFO, format="[agent1] %(levelname)s %(message)s")
log = logging.getLogger("agent1")

# ── Prompt templates ───────────────────────────────────────────────────────────

PROMPT_TEMPLATE = """\
You are a screenwriter. Output ONLY a valid JSON array. No explanation, no markdown fences.

Story config:
- Genre: {genre}
- Plot: {plot}
- Characters: {characters}
- Tone: {tone}
- Target duration: {duration_minutes} minutes
- Approximate scenes: {scene_count}

Each scene must have these exact fields:
{{
  "scene_number": 1,
  "narration": "The narration text read aloud for this scene.",
  "image_prompt": "A detailed visual description for image generation. Include style, lighting, characters present.",
  "duration_seconds": 8,
  "characters": ["Character A"]
}}

Rules:
- duration_seconds must be a positive integer between 6 and 15
- characters must be a non-empty array using the exact names from the config
- image_prompt must be rich and cinematic, mentioning character appearances
- narration must flow naturally when read aloud
- Total of all duration_seconds should be approximately {target_seconds} seconds

Return a JSON array of exactly {scene_count} scenes. Nothing else.
"""

RETRY_SUFFIX = """
IMPORTANT: Your previous response was not valid JSON or was missing required fields.
Return ONLY a raw JSON array. Do not include any text, explanation, or markdown.
Start your response with [ and end with ].
"""

# ── Status helpers ─────────────────────────────────────────────────────────────

def write_status(state: str, progress: int = 0, message: str = "") -> None:
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.write_text(
        json.dumps({"state": state, "progress": progress, "message": message}, indent=2)
    )
    log.info("status=%s progress=%d %s", state, progress, message)

# ── Config loading ─────────────────────────────────────────────────────────────

def load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"story_config.json not found at {CONFIG_PATH}")
    with open(CONFIG_PATH) as f:
        config = json.load(f)
    for key in ["genre", "tone", "target_duration_minutes", "characters"]:
        if key not in config:
            raise ValueError(f"story_config.json missing required field: '{key}'")
    return config

# ── Prompt building ────────────────────────────────────────────────────────────

def build_prompt(config: dict, retry: bool = False) -> tuple[str, int, int]:
    duration_minutes = config["target_duration_minutes"]
    target_seconds   = duration_minutes * 60
    scene_count      = max(10, round(target_seconds / 8))

    characters_str = ", ".join(
        f"{c['name']} ({c['description']})" if isinstance(c, dict) else str(c)
        for c in config["characters"]
    )

    prompt = PROMPT_TEMPLATE.format(
        genre=config["genre"],
        plot=config.get("plot", ""),
        characters=characters_str,
        tone=config["tone"],
        duration_minutes=duration_minutes,
        scene_count=scene_count,
        target_seconds=target_seconds,
    )

    if retry:
        prompt += RETRY_SUFFIX

    return prompt, scene_count, target_seconds

# ── LLM backends ───────────────────────────────────────────────────────────────

def call_ollama(prompt: str, model: str, endpoint: str) -> str:
    url = endpoint.rstrip("/") + "/api/generate"
    log.info("Ollama: model=%s endpoint=%s", model, url)
    resp = requests.post(
        url,
        json={"model": model, "prompt": prompt, "stream": False,
              "options": {"temperature": 0.7, "num_predict": 8192}},
        timeout=300,
    )
    resp.raise_for_status()
    return resp.json()["response"]


def call_vllm(prompt: str, model: str, endpoint: str) -> str:
    url = endpoint.rstrip("/") + "/v1/chat/completions"
    log.info("vLLM: model=%s endpoint=%s", model, url)
    resp = requests.post(
        url,
        json={"model": model,
              "messages": [{"role": "user", "content": prompt}],
              "temperature": 0.7, "max_tokens": 8192},
        timeout=300,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def call_huggingface(prompt: str, model: str, checkpoint_path: str | None) -> str:
    # Import lazily — only needed for this backend
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
    except ImportError:
        raise RuntimeError("Install transformers and torch to use the huggingface backend.")

    load_path = checkpoint_path or MODELS_DIR / model.replace("/", "--")
    load_path = str(load_path)
    log.info("HuggingFace: loading from %s", load_path)

    tokenizer = AutoTokenizer.from_pretrained(load_path)
    model_obj  = AutoModelForCausalLM.from_pretrained(
        load_path,
        torch_dtype=torch.float16,
        device_map="auto",
    )
    pipe = pipeline(
        "text-generation",
        model=model_obj,
        tokenizer=tokenizer,
        max_new_tokens=8192,
        temperature=0.7,
        do_sample=True,
    )
    result = pipe(prompt)
    return result[0]["generated_text"][len(prompt):]  # strip the input prompt


def call_llm(prompt: str, config: dict) -> str:
    model_cfg = config.get("models", {}).get("story", {})
    backend   = model_cfg.get("backend", "ollama")
    model     = model_cfg.get("model", "mistral-nemo")
    endpoint  = model_cfg.get("endpoint", "http://localhost:11434")
    ckpt      = model_cfg.get("checkpoint_path")

    if backend == "ollama":
        return call_ollama(prompt, model, endpoint)
    elif backend == "vllm":
        return call_vllm(prompt, model, endpoint or "http://localhost:8000")
    elif backend == "huggingface":
        return call_huggingface(prompt, model, ckpt)
    else:
        raise ValueError(f"Unknown backend '{backend}'. Choose: ollama | vllm | huggingface")

# ── Response parsing ───────────────────────────────────────────────────────────

def extract_json(raw: str) -> list:
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip()
    match = re.search(r"\[.*\]", cleaned, re.DOTALL)
    if not match:
        raise ValueError("No JSON array found in LLM response")
    return json.loads(match.group())

# ── Validation ─────────────────────────────────────────────────────────────────

REQUIRED_FIELDS = {"scene_number", "narration", "image_prompt", "duration_seconds", "characters"}

def validate_scenes(scenes: list, target_seconds: int) -> list[str]:
    if not scenes:
        return ["Scene array is empty"]

    errors = []
    total  = 0

    for i, scene in enumerate(scenes):
        prefix  = f"Scene {i + 1}"
        missing = REQUIRED_FIELDS - scene.keys()
        if missing:
            errors.append(f"{prefix}: missing fields {missing}")
            continue
        if not isinstance(scene["duration_seconds"], int) or scene["duration_seconds"] <= 0:
            errors.append(f"{prefix}: duration_seconds must be a positive integer")
        if not isinstance(scene["characters"], list) or not scene["characters"]:
            errors.append(f"{prefix}: characters must be a non-empty array")
        total += scene.get("duration_seconds", 0)

    lower, upper = target_seconds * 0.80, target_seconds * 1.20
    if not (lower <= total <= upper):
        errors.append(
            f"Total duration {total}s outside 20% tolerance of target {target_seconds}s "
            f"(allowed: {lower:.0f}–{upper:.0f}s)"
        )

    return errors

# ── Main ───────────────────────────────────────────────────────────────────────

MAX_RETRIES = 3

def run() -> None:
    write_status("running", 0, "Loading story config")

    try:
        config = load_config()
    except (FileNotFoundError, ValueError) as e:
        write_status("error", 0, str(e))
        log.error(str(e))
        sys.exit(1)

    log.info(
        "Config loaded: genre=%s duration=%smin characters=%s backend=%s model=%s",
        config["genre"],
        config["target_duration_minutes"],
        [c["name"] if isinstance(c, dict) else c for c in config["characters"]],
        config.get("models", {}).get("story", {}).get("backend", "ollama"),
        config.get("models", {}).get("story", {}).get("model", "mistral-nemo"),
    )

    scenes      = None
    last_errors = []

    for attempt in range(1, MAX_RETRIES + 1):
        write_status(
            "running",
            round((attempt - 1) / MAX_RETRIES * 80),
            f"Calling LLM (attempt {attempt}/{MAX_RETRIES})",
        )

        prompt, scene_count, target_seconds = build_prompt(config, retry=(attempt > 1))

        try:
            raw = call_llm(prompt, config)
        except requests.exceptions.ConnectionError as e:
            write_status("error", 0, f"Cannot reach LLM endpoint: {e}")
            log.error(str(e))
            sys.exit(1)
        except (requests.exceptions.RequestException, RuntimeError) as e:
            log.warning("LLM call failed (attempt %d): %s", attempt, e)
            if attempt == MAX_RETRIES:
                write_status("error", 0, f"LLM call failed after {MAX_RETRIES} attempts: {e}")
                sys.exit(1)
            time.sleep(2)
            continue

        log.info("LLM responded (%d chars)", len(raw))

        try:
            scenes = extract_json(raw)
        except (ValueError, json.JSONDecodeError) as e:
            last_errors = [f"JSON parse error: {e}"]
            log.warning("Attempt %d: %s", attempt, last_errors[0])
            continue

        last_errors = validate_scenes(scenes, target_seconds)
        if not last_errors:
            log.info("Validation passed — %d scenes, total ~%ds", len(scenes), target_seconds)
            break

        log.warning("Attempt %d validation errors: %s", attempt, last_errors)

    if last_errors:
        write_status("error", 0, f"Validation failed after {MAX_RETRIES} attempts: {last_errors}")
        log.error("Giving up after %d attempts.", MAX_RETRIES)
        sys.exit(1)

    write_status("running", 90, f"Writing {len(scenes)} scenes")
    SCENES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SCENES_PATH, "w") as f:
        json.dump(scenes, f, indent=2)
    log.info("Written: %s", SCENES_PATH)

    write_status("done", 100, f"Generated {len(scenes)} scenes successfully")
    log.info("Agent 1 complete.")


if __name__ == "__main__":
    run()
