# Trigger PRT on a Robottelo PR

Trigger Pull Request Testing (PRT) on a robottelo PR and monitor the result.

## Usage

```
/prt <PR_NUMBER> [test_path] [network_type]
```

- `test_path` — pytest node ID. If omitted, auto-detected from PR changes (see Step 0).
- `network_type` — `ipv4` or `ipv6`. Defaults to `ipv6`.

---

## Step 0 — Auto-detect impacted tests (if test_path not provided)

Get the list of files changed in the PR:

```bash
gh pr diff <PR_NUMBER> --repo SatelliteQE/robottelo --name-only
```

Then apply this logic:

**1. Directly changed test files** — any file matching `tests/foreman/**/*.py`:
Use those files directly as the pytest path (space-separated if multiple).

**2. Changed non-test files** (fixtures, helpers, constants, etc.) — find tests that import them:
```bash
# For each changed non-test file, derive its Python module path and grep for imports
# e.g. robottelo/host_helpers/repository_mixins.py -> repository_mixins
grep -rl "repository_mixins\|RepositoryCollection" tests/foreman/
```

**3. Combine** direct test files + tests that use changed helpers, deduplicate, and use as `test_path`.

**4. If the impacted set is too broad** (>5 files or whole subsystem changed), fall back to omitting `pytest:` and running the full sanity suite. Tell the user why.

**5. If only a single test function was changed**, use the full node ID with `::` (e.g. `tests/foreman/api/test_http_proxy.py::test_positive_end_to_end`).

Always confirm the detected test path with the user before triggering.

---

## Step 1 — Post PRT trigger comment

Always use `\r\n` (CRLF) line endings — the pipeline parses the comment body with `readYaml` and real newlines get stripped. Do NOT quote pytest node IDs.

Always wrap the comment body in ` ```yaml ` / ` ``` ` fences.

**With a single test:**
```bash
gh pr comment <PR_NUMBER> --repo SatelliteQE/robottelo --body "$(printf '```yaml\r\ntrigger: test-robottelo\r\npytest: -v <test_path>\r\nnetwork_type: <network_type>\r\n```')"
```

**With multiple tests — use YAML `>-` block scalar, one test per line:**
```bash
gh pr comment <PR_NUMBER> --repo SatelliteQE/robottelo --body "$(printf '```yaml\r\ntrigger: test-robottelo\r\npytest: >-\r\n  -v <test_path_1>\r\n  <test_path_2>\r\nnetwork_type: <network_type>\r\n```')"
```

**Sanity suite only (no pytest path):**
```bash
gh pr comment <PR_NUMBER> --repo SatelliteQE/robottelo --body "$(printf '```yaml\r\ntrigger: test-robottelo\r\nnetwork_type: <network_type>\r\n```')"
```

## Step 2 — Get build number and share Jenkins URL

```bash
gh pr checks <PR_NUMBER> --repo SatelliteQE/robottelo 2>&1 | grep -i "robottelo-runner"
```

Extract the build number from the status message ("PRT Build XXXXX still in progress...") and give the user the Jenkins URL:

`https://jenkins-csb-satellite-qe-satqe.dno.corp.redhat.com/job/robottelo-pr-testing/<BUILD_NUMBER>/`

## Step 3 — Poll for result

Poll every minute until no longer pending:

```bash
gh pr checks <PR_NUMBER> --repo SatelliteQE/robottelo 2>&1 | grep -i "robottelo-runner"
```

## Step 4 — Fetch pytest result from Jenkins

Once complete, use the Jenkins MCP server to get the result line:

```
getBuildLog(jobFullName="robottelo-pr-testing", buildNumber=<N>, limit=-100)
```

Look for the `=== N passed/failed ... ===` summary line and report it.

## Notes

- **YAML bug**: use `printf` with `\r\n`, not a heredoc — real newlines in the comment body get stripped by the pipeline.
- **`::` in pytest paths**: must be quoted in the YAML value or snakeyaml throws a parse error.
- **`target_url` is always empty**: the pipeline sets `statusUrl('--none--')`, so the Jenkins URL must be constructed manually from the build number in the status message.
- **Jenkins MCP**: if not configured, run `claude mcp add jenkins-satqe https://jenkins-csb-satellite-qe-satqe.dno.corp.redhat.com/mcp-server/mcp --transport http --header "Authorization: Basic <base64>"` then relaunch with `NODE_TLS_REJECT_UNAUTHORIZED=0 claude`.
