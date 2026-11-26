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

if ! LABELS=$(gh label list --repo "$REPO" --search "$LABEL" --json name); then
  echo "Failed to list labels in $REPO." >&2
  exit 1
fi

if ! jq -e --arg l "$LABEL" 'any(.[]; .name == $l)' >/dev/null <<<"$LABELS"; then
  echo "Label '$LABEL' does not exist in $REPO -- create it first (or check the name)." >&2
  exit 1
fi

echo "Fetching open, non-draft PRs targeting $BASE_BRANCH that need '$LABEL'..."

# --paginate retrieves every page rather than silently stopping at gh's
# default/explicit result limit. --slurp combines the page arrays into one
# JSON value before flattening them below.
PR_DATA=$(gh api --method GET --paginate --slurp "repos/$REPO/pulls" \
  -f state=open -f base="$BASE_BRANCH" -f per_page=100)

mapfile -t PR_ENTRIES < <(
  jq -r --arg label "$LABEL" '
    flatten[]
    | select(.draft == false)
    | {number, labels: [.labels[].name]}
    | select((.labels | index($label) | not) or (.labels | index("No-CherryPick") != null))
    | @base64
  ' <<<"$PR_DATA"
)

if [[ ${#PR_ENTRIES[@]} -eq 0 ]]; then
  echo "Nothing to label."
  exit 0
fi

echo "Found ${#PR_ENTRIES[@]} PR(s) to label or repair."

for entry in "${PR_ENTRIES[@]}"; do
  pr_data=$(printf '%s' "$entry" | base64 --decode)
  pr=$(jq -r '.number' <<<"$pr_data")
  labels=$(jq -c '.labels' <<<"$pr_data")
  has_no_cherrypick=$(jq -r 'index("No-CherryPick") != null' <<<"$labels")
  has_label=$(jq -r --arg label "$LABEL" 'index($label) != null' <<<"$labels")

  if [[ "$DRY_RUN" == true ]]; then
    if [[ "$has_label" == true ]]; then
      echo "[dry-run] would repair #$pr: flip No-CherryPick to CherryPick"
    else
      echo "[dry-run] would label #$pr with $LABEL"
      if [[ "$has_no_cherrypick" == true ]]; then
        echo "[dry-run] would also flip #$pr from No-CherryPick to CherryPick"
      fi
    fi
    continue
  fi

  updated_labels=$(jq -c --arg label "$LABEL" '
    .
    | if index($label) == null then . + [$label] else . end
    | if index("No-CherryPick") != null
      then map(select(. != "No-CherryPick"))
      | if index("CherryPick") == null then . + ["CherryPick"] else . end
      else .
      end
  ' <<<"$labels")

  echo "Updating labels on #$pr..."
  # Replace all labels in one request. Besides avoiding a partial transition,
  # this also lets a rerun repair a PR where an earlier invocation only added
  # the z-stream label before failing to flip No-CherryPick.
  gh api --method PUT "repos/$REPO/issues/$pr/labels" --input - <<<"{\"labels\":$updated_labels}"
done

echo "Done."
