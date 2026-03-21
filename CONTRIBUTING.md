# Parallel Development Guide

Each agent is developed on its own branch and owns specific files.
Do NOT touch files outside your agent's ownership list.

## Branch → File Ownership

| Branch | Files Owned |
|--------|-------------|
| `feature/agent1-story` | `agents/agent1_story.py` |
| `feature/agent2-images` | `agents/agent2_images.py` |
| `feature/agent3-audio` | `agents/agent3_audio.py` |
| `feature/agent4-motion` | `agents/agent4_motion.py` |
| `feature/agent5-assembly` | `agents/agent5_assembly.py` |
| `feature/master-agent` | `agents/master_agent.py` |

## Shared Files (touch via PR only, coordinate first)

- `requirements.txt` — add your deps in your branch, resolve conflicts on merge
- `config/story_config.example.json` — do not modify
- `docs/` — read-only during implementation
- `README.md` — do not modify

## Shared Contracts (read-only during implementation)

These are the interface contracts between agents — do not change them:

| File | Written by | Read by |
|------|-----------|---------|
| `workspace/story_config.json` | User | Agent 1 |
| `workspace/scenes.json` | Agent 1 | Agents 2, 3, 4 |
| `workspace/images/scene_{n}.png` | Agent 2 | Agent 4 |
| `workspace/audio/scene_{n}.wav` | Agent 3 | Agent 5 |
| `workspace/subtitles.srt` | Agent 3 | Agent 5 |
| `workspace/clips/scene_{n}.mp4` | Agent 4 | Agent 5 |
| `workspace/status/{agent}.json` | Each agent | Master |
| `workspace/output/final_story.mp4` | Agent 5 | User |

## Status File Schema (do not change)

```json
{ "state": "pending | running | done | error", "progress": 0, "message": "" }
```

## Workflow

1. Work only on your branch
2. Add only your deps to `requirements.txt`
3. Open a PR to `main` when done
4. PRs are merged in dependency order: 1 → 2, 3 → 4 → 5 → master
