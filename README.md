# SapnaAI 🎬

> Turn a plot-line into a 10–15 minute movie — using only open source models.

SapnaAI is a modular, AI-powered movie generation pipeline. Give it a story idea and it produces a fully narrated, subtitled video with consistent characters and scenes.

---

## How It Works

```
User story config
      │
      ▼
Agent 1 — Story Generation      (LLM: Mistral / Llama)
      │
      ├──────────────────┐
      ▼                  ▼
Agent 2 — Images     Agent 3 — Audio + Subtitles
(FLUX / SDXL)        (Coqui XTTS / Kokoro TTS)
      │
      ▼
Agent 4 — Motion / Video Clips   (Wan2.1 / AnimateDiff)
      │
      ▼
Agent 5 — Final Assembly         (FFmpeg)
      │
      ▼
output/final_story.mp4
```

---

## Agents

| Agent | Role | Docs |
|-------|------|------|
| Master | Orchestrates all agents, handles failures | [docs/master_agent.md](docs/master_agent.md) |
| Agent 1 | Story → structured scene JSON | [docs/agent1_story.md](docs/agent1_story.md) |
| Agent 2 | Scene prompts → images | [docs/agent2_images.md](docs/agent2_images.md) |
| Agent 3 | Narration text → audio + subtitles | [docs/agent3_audio.md](docs/agent3_audio.md) |
| Agent 4 | Images → animated video clips | [docs/agent4_motion.md](docs/agent4_motion.md) |
| Agent 5 | Clips + audio → final movie | [docs/agent5_assembly.md](docs/agent5_assembly.md) |

---

## Project Structure

```
SapnaAI/
├── agents/                  # Python agent implementations
│   ├── master_agent.py
│   ├── agent1_story.py
│   ├── agent2_images.py
│   ├── agent3_audio.py
│   ├── agent4_motion.py
│   └── agent5_assembly.py
├── config/
│   └── story_config.example.json
├── docs/                    # Agent plan files
│   ├── master_agent.md
│   ├── agent1_story.md
│   ├── agent2_images.md
│   ├── agent3_audio.md
│   ├── agent4_motion.md
│   └── agent5_assembly.md
├── workspace/               # Runtime workspace (gitignored)
│   ├── images/
│   ├── audio/
│   ├── clips/
│   ├── output/
│   └── status/
├── voices/                  # Reference audio clips per character
├── characters/              # Reference images / LoRA weights per character
├── requirements.txt
└── README.md
```

---

## Design Principles

- **Swappable models** — each agent declares its model in config; swap without touching pipeline logic
- **Customisable prompts** — every prompt template is editable per agent
- **Resumable** — failed scenes can be retried without restarting the full pipeline
- **Open source only** — no proprietary APIs required

---

## Quickstart

```bash
# 1. Clone
git clone https://github.com/sushkon-hwswcodes/SapnaAI.git
cd SapnaAI

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure your story
cp config/story_config.example.json workspace/story_config.json
# Edit workspace/story_config.json

# 4. Run
python agents/master_agent.py
```

---

## Model Requirements

| Agent | Recommended Model | Min VRAM |
|-------|------------------|----------|
| Story | Mistral Nemo 12B (Ollama) | 12 GB |
| Images | FLUX.1 dev | 16 GB |
| Audio | Coqui XTTS v2 | 4 GB |
| Motion | Wan2.1 | 16 GB |
| Assembly | FFmpeg (CPU) | — |

---

## Roadmap

- [x] Pipeline architecture & agent specs
- [ ] Agent implementations (Python)
- [ ] Model config system (swappable backends)
- [ ] Prompt config system (editable per stage)
- [ ] CLI interface
- [ ] Web UI
