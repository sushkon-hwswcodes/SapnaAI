#!/bin/bash
# Launches each agent in its own independent tmux session.
# You can attach to any session individually to watch it work.
#
# Usage:
#   ./scripts/launch_agents.sh          # launch all agents 2-5
#   ./scripts/launch_agents.sh 2 3      # launch only agents 2 and 3
#
# Attach to a session:
#   tmux attach -t sapnaai-agent2
#   tmux attach -t sapnaai-agent3
#   tmux attach -t sapnaai-agent4
#   tmux attach -t sapnaai-agent5
#
# List all running sessions:
#   tmux ls
#
# Detach from a session (leave it running):
#   Ctrl+B then D

set -e

REPO_ROOT="$(git rev-parse --show-toplevel)"
PARENT="$(dirname "$REPO_ROOT")"

declare -A AGENT_DIRS=(
  [2]="$PARENT/SapnaAI-agent2-images"
  [3]="$PARENT/SapnaAI-agent3-audio"
  [4]="$PARENT/SapnaAI-agent4-motion"
  [5]="$PARENT/SapnaAI-agent5-assembly"
)

declare -A AGENT_PROMPTS=(
  [2]="You are implementing Agent 2 (Image Generation) for SapnaAI. Read docs/agent2_images.md for the full spec. Implement agents/agent2_images.py only. Do not touch any other files. Read CONTRIBUTING.md for the collaboration rules."
  [3]="You are implementing Agent 3 (Audio + Subtitles) for SapnaAI. Read docs/agent3_audio.md for the full spec. Implement agents/agent3_audio.py only. Do not touch any other files. Read CONTRIBUTING.md for the collaboration rules."
  [4]="You are implementing Agent 4 (Motion + Video Clips) for SapnaAI. Read docs/agent4_motion.md for the full spec. Implement agents/agent4_motion.py only. Do not touch any other files. Read CONTRIBUTING.md for the collaboration rules."
  [5]="You are implementing Agent 5 (Final Assembly) for SapnaAI. Read docs/agent5_assembly.md for the full spec. Implement agents/agent5_assembly.py only. Do not touch any other files. Read CONTRIBUTING.md for the collaboration rules."
)

# Determine which agents to launch
if [ $# -eq 0 ]; then
  TARGETS=(2 3 4 5)
else
  TARGETS=("$@")
fi

# Check worktrees exist
for n in "${TARGETS[@]}"; do
  dir="${AGENT_DIRS[$n]}"
  if [ ! -d "$dir" ]; then
    echo "ERROR: Worktree not found: $dir"
    echo "Run ./scripts/setup_worktrees.sh first."
    exit 1
  fi
done

echo "Launching SapnaAI agents..."
echo ""

for n in "${TARGETS[@]}"; do
  dir="${AGENT_DIRS[$n]}"
  session="sapnaai-agent$n"
  prompt="${AGENT_PROMPTS[$n]}"

  if tmux has-session -t "$session" 2>/dev/null; then
    echo "  ✓ Session '$session' already running — skipping"
    continue
  fi

  echo "  → Starting session: $session"
  echo "    Directory: $dir"
  tmux new-session -d -s "$session" -c "$dir"
  tmux send-keys -t "$session" "claude '$prompt'" Enter
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "All agents launched. Attach with:"
echo ""
for n in "${TARGETS[@]}"; do
  echo "  tmux attach -t sapnaai-agent$n"
done
echo ""
echo "List all:  tmux ls"
echo "Detach:    Ctrl+B then D"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
