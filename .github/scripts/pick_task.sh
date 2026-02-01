#!/usr/bin/env bash
set -euo pipefail

# This script selects an issue for the AI agent to work on.
# It prefers `ai:in-progress` issues, falling back to `ai:todo`.
# Outputs are written to $GITHUB_OUTPUT for the calling workflow step.

GITHUB_OUTPUT=${GITHUB_OUTPUT:-/tmp/github_output}

echo "--- pick_task: starting ---" >&2

# Try to find an existing ai:in-progress issue
IN_NUM=$(gh issue list --label "ai:in-progress" --state open --limit 1 --json number --jq '.[0].number' 2>/dev/null || true)
if [ -n "$IN_NUM" ]; then
  ISSUE_NUMBER="$IN_NUM"
  SELECTED_LABEL="ai:in-progress"
else
  TODO_NUM=$(gh issue list --label "ai:todo" --state open --limit 1 --json number --jq '.[0].number' 2>/dev/null || true)
  if [ -z "$TODO_NUM" ]; then
    echo "No tasks found. Exiting." >&2
    echo "has_task=false" >> "$GITHUB_OUTPUT"
    exit 0
  fi
  ISSUE_NUMBER="$TODO_NUM"
  SELECTED_LABEL="ai:todo"
fi

echo "Selected issue #$ISSUE_NUMBER (via $SELECTED_LABEL)" >&2

# Fetch title and body using gh
ISSUE_TITLE=$(gh issue view "$ISSUE_NUMBER" --json title --jq '.title' 2>/dev/null || true)
ISSUE_BODY=$(gh issue view "$ISSUE_NUMBER" --json body --jq '.body' 2>/dev/null || true)

echo "Issue title: $ISSUE_TITLE" >&2

# Ensure ai:in-progress label exists
LABELS=$({ gh label list --limit 100 --json name --jq '.[].name' 2>/dev/null || true; } )
if ! printf '%s\n' "$LABELS" | grep -xq "ai:in-progress"; then
  gh label create "ai:in-progress" --color 1D76DB --description "In progress (claimed by AI)" || true
fi

# Claim the task if it was a todo
if [ "$SELECTED_LABEL" = "ai:todo" ]; then
  gh issue edit "$ISSUE_NUMBER" --add-label "ai:in-progress" --remove-label "ai:todo" || true
else
  gh issue edit "$ISSUE_NUMBER" --add-label "ai:in-progress" || true
fi

# Export outputs for subsequent steps
echo "has_task=true" >> "$GITHUB_OUTPUT"
echo "issue_number=$ISSUE_NUMBER" >> "$GITHUB_OUTPUT"
echo "selected_label=$SELECTED_LABEL" >> "$GITHUB_OUTPUT"

# Build the task prompt (multi-line) and append to GITHUB_OUTPUT
FILE_TREE=$(find . -maxdepth 3 -not -path '*/.*' || true)

{
  printf 'task_prompt<<EOF\n'
  printf 'REPO CONTEXT (File Tree):\n'
  printf '%s\n\n' "$FILE_TREE"
  printf 'TASK TITLE: %s\n' "$ISSUE_TITLE"
  printf 'TASK DESCRIPTION:\n'
  printf '%s\n' "$ISSUE_BODY"
  printf 'EOF\n'
} >> "$GITHUB_OUTPUT"

echo "--- pick_task: done ---" >&2
