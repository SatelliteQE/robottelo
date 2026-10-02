#!/usr/bin/env bash
# Label all open, non-draft PRs targeting a base branch (master by default)
# with a z-stream label (e.g. 6.20.z) right after a new z-stream branch is
# cut.
#
# The auto-branching workflow (.github/workflows/auto_branching.yml) creates
# the branch, the label, and the branch-cut PR itself -- but it does not
# retroactively label the PRs that were already open against master. This
# script fills that gap and is meant to be run once, by hand, right after a
# branch cut.
#
# Any labeled PR that currently carries "No-CherryPick" gets it flipped to
# "CherryPick", since being marked for backport to the new z-stream branch
# means it does need a cherry-pick after all.
#
# Requires: gh (authenticated), jq

set -euo pipefail

REPO="${REPO:-SatelliteQE/robottelo}"
BASE_BRANCH="${BASE_BRANCH:-master}"
DRY_RUN=false
LABEL=""

usage() {
  cat <<EOF
Usage: $0 <label> [options]

Options:
  --dry-run             Preview actions without making changes
  --repo <owner/repo>   Target repository (default: $REPO; or set \$REPO)
  --base <branch>       Base branch to filter PRs on (default: $BASE_BRANCH; or set \$BASE_BRANCH)
  -h, --help            Show this help

Examples:
  $0 6.20.z
  $0 6.20.z --dry-run
  $0 6.20.z --repo SatelliteQE/robottelo --base master
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --repo)
      REPO="${2:?--repo requires a value}"
      shift 2
      ;;
    --base)
      BASE_BRANCH="${2:?--base requires a value}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    -*)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
    *)
      if [[ -n "$LABEL" ]]; then
        echo "Unexpected extra argument: $1" >&2
        usage >&2
        exit 1
      fi
      LABEL="$1"
      shift
      ;;
  esac
done

if [[ -z "$LABEL" ]]; then
  usage >&2
  exit 1
fi

if ! gh label list --repo "$REPO" --search "$LABEL" --json name \
    | jq -e --arg l "$LABEL" 'any(.[]; .name == $l)' >/dev/null; then
  echo "Label '$LABEL' does not exist in $REPO -- create it first (or check the name)." >&2
  exit 1
fi

echo "Fetching open, non-draft PRs targeting $BASE_BRANCH without the '$LABEL' label..."

mapfile -t PR_ENTRIES < <(
  gh pr list --repo "$REPO" --state open --base "$BASE_BRANCH" \
    --json number,isDraft,labels --limit 300 \
  | jq -r --arg l "$LABEL" \
      '.[] | select(.isDraft == false) | select([.labels[].name] | index($l) | not) |
       [.number, ([.labels[].name] | index("No-CherryPick") != null)] | @tsv'
)

if [[ ${#PR_ENTRIES[@]} -eq 0 ]]; then
  echo "Nothing to label."
  exit 0
fi

echo "Found ${#PR_ENTRIES[@]} PR(s) to label."

for entry in "${PR_ENTRIES[@]}"; do
  pr="${entry%%$'\t'*}"
  has_no_cherrypick="${entry##*$'\t'}"

  if [[ "$DRY_RUN" == true ]]; then
    echo "[dry-run] would label #$pr with $LABEL"
    if [[ "$has_no_cherrypick" == "true" ]]; then
      echo "[dry-run] would flip #$pr from No-CherryPick to CherryPick"
    fi
    continue
  fi

  echo "Labeling #$pr..."
  gh pr edit "$pr" --repo "$REPO" --add-label "$LABEL"

  if [[ "$has_no_cherrypick" == "true" ]]; then
    echo "  #$pr had No-CherryPick -- flipping to CherryPick"
    gh pr edit "$pr" --repo "$REPO" --remove-label "No-CherryPick" --add-label "CherryPick"
  fi
done

echo "Done."
