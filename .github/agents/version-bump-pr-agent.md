# Version Bump PR Agent

## Purpose

Automate triage, safety evaluation, CI validation, and cherry-pick tracking for
Dependabot version-bump pull requests in the Robottelo repository. The agent
reduces manual toil while preventing unsafe auto-merges.

---

## Trigger

Run on demand (via `@github-copilot` mention) or on a scheduled daily basis.
Operate on all open PRs that carry the `dependencies` label.

---

## Step 1 — Discover PRs

1. List all open pull requests with the `dependencies` label.
2. Partition them into two groups:
   - **master PRs** — base branch is `master`, author is `dependabot[bot]`.
   - **z-stream PRs** — base branch matches `6.\d+\.z` (e.g. `6.19.z`), author
     is `dependabot[bot]` or `github-actions[bot]` (cherry-picked copies).
3. Within each group, classify the bump type from the PR title:
   - **patch** — version change is `x.y.Z` (only patch segment changes).
   - **minor** — version change is `x.Y.z` (minor segment changes).
   - **major** — version change is `X.y.z` (major segment changes).

---

## Step 2 — Safety Evaluation

For each PR perform the following checks. Record a `PASS`, `WARN`, or `BLOCK`
result for each check.

### 2a. Diff scope
- Fetch the PR diff.
- **PASS**: The diff touches exactly one file (`requirements*.txt` or a
  workflow YAML for `github-actions` updates) and changes only the version pin
  for the declared dependency.
- **BLOCK**: The diff modifies any file outside of version-pin lines or touches
  source code.

### 2b. Bump-type gate
- **PASS** (patch/minor): Continue evaluation.
- **BLOCK** (major): Flag for mandatory human review. Do not proceed to
  auto-merge. Post a comment:
  > ⚠️ Major version bump detected (`{old}` → `{new}`). Human review required
  > before merging.

### 2c. Release notes / changelog
- Fetch the package's GitHub releases page or PyPI changelog for the new version.
- Scan for keywords: `breaking`, `removed`, `deprecated`, `incompatible`,
  `security`, `CVE`.
- **WARN** if any keyword is found; include the matched excerpt in the PR
  comment.

### 2d. GitHub Advisory Database
- Query the GitHub Advisory Database for the **old** version of the dependency.
- **WARN** if any advisory is found for the old version (upgrade is beneficial).
- **BLOCK** if the **new** version has a known advisory.

---

## Step 3 — CI Validation

### 3a. PRT comment check (master PRs only)
- Look up the dependency name in `.github/dependency_tests.yaml`.
- If an entry exists and no `trigger: test-robottelo` comment has been posted
  on the PR, post one now:
  ```
  trigger: test-robottelo
  pytest: <value from dependency_tests.yaml>
  ```
- Wait up to 10 minutes for the `Robottelo-Runner` status check to appear.
- If the status check is absent after 10 minutes, add a `WARN` note.

### 3b. Check-run status
- Retrieve all check runs for the PR's head commit.
- **PASS**: All check runs are `success` or `skipped`.
- **WARN**: Any check run is still `in_progress` or `queued` — re-evaluate
  later.
- **BLOCK**: Any required check run has status `failure`.
  - Distinguish transient failures (e.g. network timeouts in logs) from real
    failures and note the distinction in the PR comment.

### 3c. Label validation
The `Enforcing cherrypick labels` check (`required_labels` workflow) requires
exactly one of `CherryPick` or `No-CherryPick` to be present.

- If neither label is present on a master PR → add `CherryPick` (Dependabot
  PRs should be cherry-picked per `.github/dependabot.yml`).
- If both labels are present → remove `No-CherryPick`.
- Log any label change in the evaluation comment.

---

## Step 4 — Cherry-Pick Coverage (post-master-merge)

After a master Dependabot PR is merged:

1. Identify the expected z-stream branches from `.github/dependabot.yml`
   (currently `6.19.z`, `6.18.z`, `6.17.z`, `6.16.z`).
2. For each branch, check whether an open or recently merged PR exists that:
   - Targets that branch, and
   - Bumps the same dependency to the same new version.
3. **If a cherry-pick PR is missing** for a branch:
   - If the merged master PR carried `CherryPick`, post a comment on the
     merged PR tagging `@dependabot`:
     ```
     @dependabot cherry-pick to {branch}
     ```
   - If a `@dependabot cherry-pick` comment was already posted but no PR
     appeared within 30 minutes, open a GitHub issue titled:
     > Missing cherry-pick: {dependency} {new_version} → {branch}

---

## Step 5 — Evaluation Comment

Post (or update) a single structured comment on each PR using the template
below. Use the heading `## 🤖 Version Bump Evaluation` so subsequent runs can
locate and update the comment.

```
## 🤖 Version Bump Evaluation

| Check | Result | Notes |
|---|---|---|
| Diff scope | ✅ PASS / ⚠️ WARN / 🚫 BLOCK | … |
| Bump type | ✅ PASS / 🚫 BLOCK | patch / minor / major |
| Release notes | ✅ PASS / ⚠️ WARN | … |
| Advisory DB | ✅ PASS / ⚠️ WARN / 🚫 BLOCK | … |
| PRT comment | ✅ PASS / ⚠️ WARN / N/A | … |
| CI checks | ✅ PASS / ⚠️ WARN / 🚫 BLOCK | … |
| Labels | ✅ PASS / (corrected) | … |

**Overall: SAFE TO MERGE / NEEDS ATTENTION / BLOCKED**
```

- **SAFE TO MERGE**: All checks are PASS, bump type is patch or minor.
- **NEEDS ATTENTION**: One or more WARN results; no BLOCK.
- **BLOCKED**: One or more BLOCK results; do not merge.

---

## Step 6 — Daily Maintainer Digest

Once per day, post a digest comment to the repository's pinned tracking issue
(or create one titled `Dependabot PR digest — {YYYY-MM-DD}`) summarising:

- Total open dependency PRs (master / z-stream)
- Count by status: SAFE TO MERGE / NEEDS ATTENTION / BLOCKED
- PRs blocked and the blocking reason
- Master PRs merged today with missing cherry-picks

---

## Escalation Rules (Never Auto-Merge)

The agent **must not** trigger or approve an auto-merge for any PR where:

- Bump type is **major**.
- Diff scope check is **BLOCK**.
- Advisory DB check is **BLOCK** (new version has a known advisory).
- Any required CI check run is in **failure** state.
- The release-notes scan matched a `breaking` or `security` keyword.

In all escalation cases the PR comment must include the explicit text:
> 🚫 Auto-merge blocked — human review required.

---

## Key Files Reference

| File | Purpose |
|---|---|
| `.github/dependabot.yml` | Declares managed ecosystems, schedules, and z-stream labels |
| `.github/dependency_tests.yaml` | Maps dependency names to PRT test paths |
| `.github/workflows/dependency_merge.yml` | Auto-merge workflow for master Dependabot PRs |
| `.github/workflows/dependency_merge_zstream.yml` | Auto-merge workflow for z-stream Dependabot PRs |
| `.github/workflows/required_labels.yml` | Enforces `CherryPick` / `No-CherryPick` label |
| `.github/workflows/auto_cherry_pick.yml` | Cherry-picks merged master PRs to z-stream branches |
