#!/usr/bin/env bash
# Usage: ./scripts/copy-epic-prompt.sh EP-01
# Substitutes the epic ID into the agent prompt template and copies it to clipboard.

set -euo pipefail

EPIC_ID="${1:-}"

if [[ -z "$EPIC_ID" ]]; then
    echo "Usage: $0 <epic-id>  (e.g. EP-01)"
    exit 1
fi

if [[ ! "$EPIC_ID" =~ ^EP-[0-9]{2}$ ]]; then
    echo "Error: Epic ID must be in the format EP-NN (e.g. EP-01, EP-09)"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TEMPLATE="$REPO_ROOT/docs/prompts/epic-development-agent.md"
EPICS_DIR="$REPO_ROOT/docs/project-planning/epics"

if [[ ! -f "$TEMPLATE" ]]; then
    echo "Error: Prompt template not found at $TEMPLATE"
    exit 1
fi

# Validate that an epic file exists for the given ID
EPIC_NUM="${EPIC_ID#EP-}"  # strip "EP-" prefix → "01"
EPIC_FILE=$(find "$EPICS_DIR" -name "epic-${EPIC_NUM}-*.md" 2>/dev/null | head -1)

if [[ -z "$EPIC_FILE" ]]; then
    echo "Error: No epic file found matching 'epic-${EPIC_NUM}-*.md' in $EPICS_DIR"
    echo ""
    echo "Available epics:"
    ls "$EPICS_DIR"
    exit 1
fi

echo "Found epic: $(basename "$EPIC_FILE")"

# Extract the prompt section (everything after the "## PROMPT" heading)
# then substitute the epic ID placeholder
PROMPT=$(awk '/^## PROMPT$/{found=1; next} found{print}' "$TEMPLATE" \
         | sed "s/{{EPIC_ID}}/$EPIC_ID/g")

if [[ -z "$PROMPT" ]]; then
    echo "Error: Could not extract ## PROMPT section from $TEMPLATE"
    exit 1
fi

# Copy to clipboard — try tools in order of preference
if command -v xclip &>/dev/null; then
    printf '%s' "$PROMPT" | xclip -selection clipboard
elif command -v wl-copy &>/dev/null; then
    printf '%s' "$PROMPT" | wl-copy
elif command -v xsel &>/dev/null; then
    printf '%s' "$PROMPT" | xsel --clipboard --input
else
    echo "Error: No clipboard tool found. Install one of: xclip, wl-copy, xsel"
    echo ""
    echo "  sudo apt install xclip"
    exit 1
fi

echo "Prompt for $EPIC_ID copied to clipboard — ready to paste."
