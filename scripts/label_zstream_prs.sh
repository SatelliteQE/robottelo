#!/usr/bin/env bash
# Label all open, non-draft PRs targeting `master` with a z-stream label
# (e.g. 6.20.z) right after a new z-stream branch is cut.
#
# The auto-branching workflow (.github/workflows/auto_branching.yml) creates
# the branch, the label, and the branch-cut PR itself -- but it does not
# retroactively label the PRs that were already open against master. This
# script fills that gap and is meant to be run once, by hand, right after a
# branch cut.
#
# Usage:
#   scripts/label_zstream_prs.sh 6.20.z
#   scripts/label_zstream_prs.sh 6.20.z --dry-run
#
# Requires: gh (authenticated), jq

set -euo pipefail

REPO="SatelliteQE/robottelo"

LABEL="${1:-}"
DRY_RUN=false
if [[ "${2:-}" == "--dry-run" ]]; then
  DRY_RUN=true
fi

if [[ -z "$LABEL" ]]; then
  echo "Usage: $0 <label, e.g. 6.20.z> [--dry-run]" >&2
  exit 1
fi

if ! gh label list --repo "$REPO" --search "$LABEL" --json name \
    | jq -e --arg l "$LABEL" 'any(.[]; .name == $l)' >/dev/null; then
  echo "Label '$LABEL' does not exist in $REPO -- create it first (or check the name)." >&2
  exit 1
fi

echo "Fetching open, non-draft PRs targeting master without the '$LABEL' label..."

mapfile -t PRS < <(
  gh pr list --repo "$REPO" --state open --base master \
    --json number,isDraft,labels --limit 300 \
  | jq -r --arg l "$LABEL" \
      '.[] | select(.isDraft == false) | select([.labels[].name] | index($l) | not) | .number'
)

if [[ ${#PRS[@]} -eq 0 ]]; then
  echo "Nothing to label."
  exit 0
fi

echo "Found ${#PRS[@]} PR(s) to label: ${PRS[*]}"

for pr in "${PRS[@]}"; do
  if [[ "$DRY_RUN" == true ]]; then
    echo "[dry-run] would label #$pr with $LABEL"
  else
    echo "Labeling #$pr..."
    gh pr edit "$pr" --repo "$REPO" --add-label "$LABEL"
  fi
done

echo "Done."
