---
# ============================================================
# SETUP INSTRUCTIONS
# ============================================================
# 1. Create a GitHub PAT (classic or fine-grained) with Contents:write
#    on the SatelliteQE/robottelo.wiki repository.
# 2. Add it as a repository secret named WIKI_SYNC_PAT on
#    SatelliteQE/robottelo (Settings → Secrets → Actions).
# 3. After editing this file's frontmatter, recompile:
#      gh aw compile .github/workflows/wiki-sync.md
# ============================================================

on:
  schedule:
    - cron: "0 22 * * 5"  # Every Friday at 22:00 UTC
  workflow_dispatch:
    inputs:
      apply:
        description: "Apply proposed changes to the wiki (default: create issue only)"
        type: boolean
        default: false

description: >
  Analyzes recent commits to master for documentation-relevant changes
  and either reports proposed wiki updates as a GitHub issue (default)
  or applies them directly to the SatelliteQE/robottelo wiki (when apply=true).

permissions:
  contents: read
  issues: read
  metadata: read

tools:
  edit:
  github:
    toolsets: [repos, issues]
    mode: local
  cache-memory:
  web-fetch:

network:
  firewall: true
  allowed:
    - defaults
    - github

safe-outputs:
  create-issue:
    title-prefix: "[wiki-sync] "
    labels: [documentation]
    close-older-issues: true
    expires: 21
  jobs:
    push-to-wiki:
      description: "Writes proposed wiki changes to SatelliteQE/robottelo.wiki and pushes them."
      runs-on: ubuntu-latest
      steps:
        - name: Apply wiki changes
          env:
            WIKI_SYNC_PAT: ${{ secrets.WIKI_SYNC_PAT }}
          run: |
            set -euo pipefail

            if [ -z "${WIKI_SYNC_PAT:-}" ]; then
              echo "::error::WIKI_SYNC_PAT secret is not set. See .github/workflows/wiki-sync.md for setup instructions."
              exit 1
            fi

            echo "::add-mask::${WIKI_SYNC_PAT}"
            git -c "http.extraHeader=Authorization: Bearer ${WIKI_SYNC_PAT}" \
              clone https://github.com/SatelliteQE/robottelo.wiki.git wiki
            cd wiki

            python3 - <<'PYEOF'
            import json, os, sys

            output_file = os.environ.get("GH_AW_AGENT_OUTPUT", "")
            if not output_file or not os.path.isfile(output_file):
                print("No agent output file found; nothing to apply.")
                sys.exit(0)

            with open(output_file) as f:
                data = json.load(f)

            items = [i for i in data.get("items", []) if i.get("type") == "push_to_wiki"]
            if not items:
                print("No push_to_wiki items in agent output; nothing to apply.")
                sys.exit(0)

            wrote = []
            for item in items:
                for change in item.get("changes", []):
                    filename = change.get("filename", "")
                    # Guard: only .md or .rest filenames (robottelo wiki has both),
                    # no path traversal, no hidden files.
                    # Unicode characters (e.g. non-breaking hyphen in
                    # Helpers-Best-Practices-‐-Guide.md) are intentionally allowed.
                    if (
                        not (filename.endswith(".md") or filename.endswith(".rest"))
                        or "/" in filename
                        or filename.startswith(".")
                    ):
                        print(f"Skipping unsafe filename: {filename!r}", file=sys.stderr)
                        continue
                    print(f"Writing {filename}")
                    with open(filename, "w", encoding="utf-8") as fout:
                        fout.write(change["content"])
                    wrote.append(filename)

            if not wrote:
                print("No valid files to write; exiting.")
                sys.exit(0)
            PYEOF

            git config user.email "github-actions[bot]@users.noreply.github.com"
            git config user.name "github-actions[bot]"
            git add -A

            if git diff --staged --quiet; then
              echo "No changes to commit — wiki is already up to date."
              exit 0
            fi

            COMMIT_MSG=$(python3 - <<'PYEOF'
            import json, os, sys
            with open(os.environ["GH_AW_AGENT_OUTPUT"]) as f:
                data = json.load(f)
            items = [i for i in data.get("items", []) if i.get("type") == "push_to_wiki"]
            msg = (items[0].get("commit_message") if items else None) or "docs: weekly wiki sync [automated]"
            print(msg)
            PYEOF
            )

            git commit -m "${COMMIT_MSG}"

            if ! git -c "http.extraHeader=Authorization: Bearer ${WIKI_SYNC_PAT}" push; then
              echo "::warning::Push failed (possible conflict). A summary issue was still created by the agent."
              exit 1
            fi

            echo "Wiki updated: ${COMMIT_MSG}"
---

# Weekly Wiki Sync

You are a documentation maintenance agent for the **Robottelo** project — a
pytest-based functional test suite for **Red Hat Satellite** and **Foreman**.
Robottelo tests multiple interfaces (API, CLI, UI) and provides a layered
framework of fixtures, helpers, and host abstractions used across hundreds of
test modules.

The wiki lives at `SatelliteQE/robottelo` (GitHub wiki, repository name:
`SatelliteQE/robottelo.wiki`). Your job is to keep it accurate and
up-to-date with the current state of the codebase.

---

## Step 1: Determine the starting commit

Call `cache-memory read` with key `wiki_sync_last_sha`.

- If a SHA is found, use it as `base_sha`.
- If not found (first run), use the commit SHA from exactly 7 days ago as
  `base_sha`. Get this by listing recent commits to `SatelliteQE/robottelo`
  on `master` and selecting the oldest one from the past 7 days.

List all commits to `master` in `SatelliteQE/robottelo` since `base_sha`.
Record the SHA of the most-recent commit as `head_sha`.

If there are **no commits** since `base_sha`, write `head_sha = base_sha` and
proceed to Step 5 (update SHA cache) — do not create an issue or push anything.

---

## Step 2: Identify doc-relevant changes

For each commit, fetch the list of files changed. Review the full set of
changed files and commit messages across all commits this week.

Use your judgment to determine whether any changes are **documentation-relevant**.
A change is doc-relevant if it affects something a contributor to Robottelo
would need to know about when writing tests, adding fixtures, or working with
the framework. Examples include:

- **Host abstractions**: changes to `robottelo/hosts.py` (class hierarchy,
  new methods on `Satellite`, `Capsule`, or `ContentHost`, changes to
  `ui_session`, `api`, or `cli` accessors)
- **Host helpers**: changes to any file in `robottelo/host_helpers/`
  (`api_factory.py`, `cli_factory.py`, `ui_factory.py`, `*_mixins.py`,
  `repository_mixins.py`) — new helpers, renamed helpers, changed signatures
- **Utilities**: new modules or changed APIs in `robottelo/utils/` that
  contributors would call directly
- **Pytest markers**: new or changed markers in `pytest_plugins/` that affect
  how tests are selected or parameterized (e.g., `rhel_ver_match`,
  `rhel_ver_list`, `destructive`, `no_containers`)
- **Core fixtures**: new or changed fixture patterns in `pytest_fixtures/core/`
  (especially `broker.py`, `contenthosts.py`, `sat_cap_factory.py`, `xdist.py`)
- **Setup and dependencies**: changes to `requirements.txt`,
  `requirements-optional.txt`, `pyproject.toml` (Python version, new required
  packages), or `Makefile` (new or renamed make targets)
- **Configuration**: changes to `conf/*.yaml.template` that require contributors
  to update their local config
- **Upgrade test patterns**: changes to `robottelo/utils/shared_resource.py` or
  the `tests/new_upgrades/` structure that establish or change how upgrade
  scenarios are written
- **Contributing or review conventions**: changes to `docs/` or `CODEOWNERS`
  that affect how contributors work

Changes that are **not** doc-relevant include: individual test module changes
(`tests/foreman/**`, `tests/new_upgrades/**`), CI/CD workflow changes
(`.github/workflows/`), lint or formatting fixes, and internal refactors with
no user-visible behavior change.

If **no doc-relevant changes** are found, skip to Step 5 (update SHA cache)
and stop — do not create an issue or push anything.

---

## Step 3: Understand what changed

For each doc-relevant change identified in Step 2, fetch the current content
of the relevant source files from `SatelliteQE/robottelo` (default branch).
Read them carefully and note exactly what is new, changed, or removed and how
it differs from what the current wiki describes.

---

## Step 4: Fetch current wiki content

Fetch the current content of all wiki pages from `SatelliteQE/robottelo.wiki`.
At minimum, retrieve:

- `Home.md`
- `Helpers-Best-Practices-‐-Guide.md`
- `Robottelo-Contributing-Guidelines.md`
- `Robottelo-Setup.md`
- `Pytest-Markers.md`
- `Test-Case-Naming-Conventions.md`
- `Robottelo-Reviewers-Guide.md`

Also check whether any of these pages might be relevant to the changes found:

- `Jira-Issue-Handler.md` (if issue handler code changed)
- `Working-With-git.rest` (if git workflow or worktree docs need updating)
- `Robottelo-Pull-Request-Testing-(PRT)-Process.md` (if PRT process changed)

---

## Step 5: Identify gaps and update SHA cache

For each wiki page, identify **specific sections** that are outdated, missing,
or incorrect based on the code changes found in Step 3. For each gap, note:
which wiki page, which section, what the old content is, what the new content
should be, and which commit + file justifies the change.

Write `head_sha` to `cache-memory` under key `wiki_sync_last_sha` now
(regardless of whether gaps were found).

**Hard limits — always obey these:**

1. **Evidence-only**: Only flag a gap if you have clear evidence from an
   actual code change. Do not speculate about undocumented behavior.
2. **Surgical edits only**: Propose targeted section-level updates. Do not
   rewrite entire pages from scratch.
3. **No removals**: Do not remove or rename existing sections. You may update
   content within them or add new sections.
4. **Blast radius**: Change at most **3 wiki pages** per run, and at most
   **100 lines net** across all pages.
5. **New pages only for major features**: Only propose creating a new wiki page
   if a major new contributor-facing feature has no existing coverage at all.
   New pages count toward the 3-page limit.

---

## Step 6A: Analysis mode (default)

*Use this step when triggered by schedule or by `workflow_dispatch` with
`apply: false`.*

Create a `[wiki-sync]` issue titled
`[wiki-sync] Documentation review — week of {YYYY-MM-DD}` that contains:

1. **Commits analyzed**: `{base_sha}` → `{head_sha}` with a link to the
   compare view
   (`https://github.com/SatelliteQE/robottelo/compare/{base_sha}...{head_sha}`)
2. **Doc-relevant changes found**: bullet list of what changed and why it
   matters for docs
3. **Proposed wiki updates**: for each affected page and section:
   - What changed in the code (with commit reference and link)
   - The proposed new section content as a fenced markdown code block labelled
     with the filename and section name
   - Exactly where in the page the change should go (e.g., "replace the
     existing `## host_helpers` subsection" or "add after the `## utils`
     section")
4. If no doc-relevant changes were found despite commits existing:
   "No documentation updates required for this week's changes."

End the issue with:

> To apply these changes, trigger the **Weekly Wiki Sync** workflow from the
> Actions tab with **Apply: true**.

---

## Step 6B: Apply mode

*Use this step when triggered by `workflow_dispatch` with `apply: true`.*

If there are no concrete proposed changes, use the `noop` output and stop.

Call the `push-to-wiki` tool with:

- `changes`: JSON array of
  `{"filename": "PageName.md", "content": "<complete updated page content>"}` —
  one entry per page being updated. Provide the **full updated file content**,
  not a diff. Use `PageName.rest` for `Working-With-git.rest`.
- `commit_message`: A concise, imperative-mood git commit message (e.g.,
  `"docs: update Helpers Best Practices with new repository_mixins details"`).
  Prefix with `docs:`.

After calling `push-to-wiki`, also create a brief `[wiki-sync]` issue titled
`[wiki-sync] Applied documentation updates — week of {YYYY-MM-DD}` summarizing:
- Which wiki pages were updated
- What was changed and why (with links to the triggering commits)
