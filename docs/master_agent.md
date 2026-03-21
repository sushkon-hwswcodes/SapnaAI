# Master Agent — Orchestrator

## Role
Spawns and monitors all 5 worker agents. Coordinates dependencies, handles failures, and reports final output to the user.

## Responsibilities
- Read `story_config.json` and pass it to Agent 1
- Block Agents 2 & 3 until Agent 1 signals completion
- Spawn Agents 2 & 3 simultaneously once `scenes.json` is written
- Spawn Agent 4 as soon as Agent 2 writes its first image to disk
- Spawn Agent 5 only after both Agents 3 & 4 signal `done`
- Poll all agent status files every 5 seconds
- Surface errors and support per-scene retry without full pipeline restart
- Report final output path to the user on completion

## Workspace Layout
```
/workspace/
  story_config.json        # Input: user story config
  scenes.json              # Agent 1 output, consumed by Agents 2, 3, 4
  images/
    scene_{n}.png          # Agent 2 output
  audio/
    scene_{n}.wav          # Agent 3 output
  subtitles.srt            # Agent 3 output
  clips/
    scene_{n}.mp4          # Agent 4 output
  output/
    final_story.mp4        # Agent 5 output
  status/
    agent1.json            # { state, progress, message }
    agent2.json
    agent3.json
    agent4.json
    agent5.json
```

## Agent Status Schema
Each agent writes to `/workspace/status/{agent_id}.json`:
```json
{
  "state": "pending | running | done | error",
  "progress": 0,
  "message": "human-readable status"
}
```

## Startup Sequence
1. Validate `story_config.json` exists and is well-formed
2. Initialise all status files to `{ state: "pending", progress: 0 }`
3. Spawn **Agent 1**. Wait for `status/agent1.json` → `done`
4. Spawn **Agent 2** and **Agent 3** simultaneously
5. Watch `images/` folder — spawn **Agent 4** on first image write
6. Wait for `status/agent3.json` AND `status/agent4.json` → `done`
7. Spawn **Agent 5**. Wait for `status/agent5.json` → `done`
8. Return `output/final_story.mp4` to user

## Dependency Graph
```
Agent 1 (story)
    ↓
Agent 2 (images) ──► Agent 4 (motion)  ──┐
Agent 3 (audio)  ──────────────────────── Agent 5 (assembly)
```

## Error Handling
- If any agent enters `error` state, halt all downstream agents
- Log the full error from the agent's status message
- Expose a retry command that re-runs only the failed agent and its dependents
- Individual failed scenes can be re-queued without restarting the full pipeline

## Inputs
| File | Description |
|------|-------------|
| `story_config.json` | Genre, characters, tone, target duration |

## Outputs
| File | Description |
|------|-------------|
| `output/final_story.mp4` | Finished video with audio and subtitles |
