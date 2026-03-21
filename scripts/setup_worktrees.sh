#!/bin/bash
# Creates a git worktree + branch for each agent.
# Run once from the main repo root.

set -e

REPO_ROOT="$(git rev-parse --show-toplevel)"
PARENT="$(dirname "$REPO_ROOT")"

AGENTS=(
  "agent2-images:feature/agent2-images:agents/agent2_images.py"
  "agent3-audio:feature/agent3-audio:agents/agent3_audio.py"
  "agent4-motion:feature/agent4-motion:agents/agent4_motion.py"
  "agent5-assembly:feature/agent5-assembly:agents/agent5_assembly.py"
)

echo "Setting up worktrees from: $REPO_ROOT"

for entry in "${AGENTS[@]}"; do
  name="${entry%%:*}"
  rest="${entry#*:}"
  branch="${rest%%:*}"
  file="${rest#*:}"

  worktree_path="$PARENT/SapnaAI-$name"

  if [ -d "$worktree_path" ]; then
    echo "  ✓ $worktree_path already exists, skipping"
    continue
  fi

  echo "  → Creating worktree: $worktree_path ($branch)"
  git worktree add -b "$branch" "$worktree_path" main

  echo "    Pushing branch $branch..."
  git -C "$worktree_path" push -u origin "$branch" 2>/dev/null || true
done

echo ""
echo "Worktrees ready:"
git worktree list
