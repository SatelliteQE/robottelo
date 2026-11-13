# Robottelo Pull Request Testing (PRT) Process

**Source**: [PRT Wiki Page](https://github.com/SatelliteQE/robottelo/wiki/Robottelo-Pull-Request-Testing-(PRT)-Process)

---

## Introduction

The Pull Request Testing (PRT) process ensures the quality and stability of code changes introduced through pull requests. It provides an automated and systematic approach to testing via Jenkins.

## PRT Process Steps

### Step 1: Pull Request Submission

A contributor creates a pull request from their forked repository to the main Robottelo repository.

### Step 2: PRT Comment Initiation

The PRT process is initiated by the PR author writing a PRT comment in the PR containing:

- **Trigger Statement**: e.g. `trigger: test-robottelo` — required for Jenkins to identify the request
- **Test Details**: Which tests to run and any specific configurations

Write the entire trigger as a **single-line YAML flow mapping**, including any nested `env`,
`theforeman`, or `Katello` mappings. Put the whole mapping in one comment. This avoids Jenkins
comment parsing problems that can occur with multiline input; putting only a nested mapping on one
line does not make the whole comment single-line. **Do not include a trailing newline** (LF or CRLF)
after the closing `}`: it can also cause Jenkins parsing problems.

When posting from a file, use `printf '%s'` rather than `echo` or a heredoc, which add a newline:

```shell
printf '%s' "{trigger: test-robottelo, pytest: 'tests/foreman/api/test_product.py::test_positive_sync'}" > /tmp/prt-comment.txt
gh pr comment <pr-number> --body-file /tmp/prt-comment.txt
```

Check that the file's final byte is `}` before posting, and that the posted comment has no trailing
newline. Copying examples from a code block can also include a newline.

Quote the `pytest` value as a YAML string. Keep shell quotes inside that string when needed for
expressions or parametrized node IDs. For example, YAML double quotes can surround a value containing
shell single quotes:

```yaml
{trigger: test-robottelo, pytest: "tests/foreman/cli/test_repository.py -k 'redhat_cdn or rh_repo'"}
```

For a parametrized node ID, retain shell quotes around the brackets as well:

```yaml
{trigger: test-robottelo, pytest: "'tests/foreman/cli/test_rhcloud_inventory.py::test_positive_register_insights_client_host[rhel10-ipv4]'"}
```

Before posting, validate that the entire comment parses as a YAML mapping and check that the parsed
`pytest` string and nested options have the intended values. Check that node IDs exist, preserve
brackets and quotes in parametrized node IDs, and include upstream PR overrides only when needed.
Avoid secrets: PR comments are visible to anyone with access to the pull request.

### Step 3: Automated Testing

Once the PRT comment is added:

- The trigger statement automatically triggers the Jenkins job
- Jenkins executes the specified tests based on the provided details
- There is a **5-minute delay** before PRT picks up the request (for resource allocation and queue management)

### Step 4: Review and Reporting

Results are reported via:

- **GitHub Status API**: Clear pass/fail indication on the PR page
- **Jenkins Build Number**: Displayed for cross-referencing build details
- There is a delay in reporting the results back. It can range from lower tens of minutes to hours, depending on the test setup and complexity.
---

## Usage Examples

### Example 1: Basic PRT Comment

Runs the default **Sanity Test Suite**:

```yaml
{trigger: test-robottelo}
```

### Example 2: Using pytest Options

Run specific tests or use pytest options:

```yaml
{trigger: test-robottelo, pytest: "tests/foreman/api/test_product.py -k 'test_positive_create_product_and_update_gpg'"}
```

Select and run multiple tests using the `or` keyword:

```yaml
{trigger: test-robottelo, pytest: "tests/foreman/cli/test_satellitesync.py -k 'version_custom_repo or library_custom_repo or repository_docker'"}
```

### Example 3: Running Tests for Airgun, Nailgun, or Broker PRs

Specify PR numbers for dependent library PRs:

```yaml
{trigger: test-robottelo, pytest: "tests/foreman/api/test_product.py -k 'test_positive_create_product_and_update_gpg'", airgun: 458, nailgun: 227, broker: 282}
```

### Example 4: Running Tests for Provisioning Component

```yaml
{trigger: test-robottelo, pytest: 'tests/foreman/api/test_provisioning.py -k test_rhel_ipxe_provisioning', provisioning: true}
```

### Example 5: Running Tests for Custom Inventory and Pod Size

```yaml
{trigger: test-robottelo, pytest: "tests/foreman/api/test_product.py -k 'test_positive_create_product_and_update_gpg'", inventory: '<inventory name>', pod_resources_size: large}
```

- `inventory`: Ansible inventory name from satlab
- `pod_resources_size`: Set the pod resource size (e.g. `large`)

### Example 6: Running Tests with Environment Variables

```yaml
{trigger: test-robottelo, pytest: 'tests/foreman/ui/test_repository.py::test_positive_sync_yum_repo_and_verify_content_checksum', env: {ROBOTTELO_ui__record_video: true}}
```

> **Warning**: Do not pass sensitive information or secrets as environment variables in PRT comments. They are visible to anyone with access to the pull request.

### Example 7: Running Upgrade All Tier Tests

```yaml
{trigger: test-robottelo, pytest: 'tests/foreman/api/test_product.py -k test_positive_create_product_and_update_gpg', env: {ROBOTTELO_server__deploy_workflows__product: 'deploy-satellite-upgrade', ROBOTTELO_server__deploy_arguments__deploy_rhel_version: '9', ROBOTTELO_server__deploy_arguments__deploy_sat_version: '6.20', ROBOTTELO_server__deploy_arguments__deploy_snap_version: 'ystream', BROKER_AnsibleTower__inventory: 'osp-rhos01-satellite-upgrade'}}
```
### Example 8: Running Upgrade Scenario tests with specific from and to versions

```yaml
{trigger: test-robottelo, pytest: '-n 2 tests/new_upgrades/test_rhcloud_iop.py', env: {ROBOTTELO_server__xdist_behavior: 'run-on-one', ROBOTTELO_upgrade__from_version: '6.19', ROBOTTELO_upgrade__to_version: 'stream'}}
```

### Example 9: Running Tests Using Specific Fixtures

Use `--uses-fixtures` to execute all tests that use a specific fixture:

```yaml
{trigger: test-robottelo, pytest: '--uses-fixtures rhel_contenthost tests/foreman/'}
```

You can specify multiple fixtures: `--uses-fixtures rhel_contenthost rhel7_contenthost`

### Example 10: Running Tests Against Upstream PRs

For PRs depending on open upstream PRs in theforeman and Katello orgs:

```yaml
{trigger: test-robottelo, pytest: "tests/foreman/api/test_product.py -k 'test_positive_create_product_and_update_gpg'", theforeman: {foreman: 10138, foreman-installer: 930}, Katello: {katello: 10977}}
```

### Example 11: Running Tests Against Upstream PRs with Specific RHEL Version

Use `deploy_rhel_version` to specify the Satellite RHEL version:

```yaml
{trigger: test-robottelo, pytest: "tests/foreman/api/test_product.py -k 'test_positive_create_product_and_update_gpg'", deploy_rhel_version: 9, theforeman: {foreman: 10138, foreman-installer: 930}, Katello: {katello: 10977}}
```

### Example 12: Running Tests with IPv6 Environment

```yaml
{trigger: test-robottelo, pytest: 'tests/foreman/ui/test_repository.py::test_positive_sync_yum_repo_and_verify_content_checksum', network_type: ipv6}
```

---

## Important Notes

- PRT with upstream PR packit builds can only run against the `master` branch.
- You may only specify repositories that have packit builds (look for `rpm-build:rhel-8-x86_64` CI check)
- Only one PR number per repo is supported; for multiple PRs from the same repo, ask the author to create a combined PR
- Only `theforeman` and `Katello` organizations are supported for upstream PRs
- There is a 5-minute delay before PRT starts picking up your request
- There is a delay in reporting the results back. It can range from lower tens of minutes to hours, depending on the test setup and complexity.
---

## Satellite RHEL Version Defaults for PRT Jobs

| Satellite Version/Branch | Supported RHEL Versions | Default RHEL Version for PRT |
|--------------------------|-------------------------|------------------------------|
| 6.16                     | rhel8, rhel9            | rhel9                        |
| 6.17                     | rhel9                   | rhel9                        |
| 6.18                     | rhel9                   | rhel9                        |
| 6.19                     | rhel9                   | rhel9                        |
| stream                   | rhel9                   | rhel9                        |

---

## FAQ

**Q: How do I initiate PRT for my pull request?**
A: Add a PRT comment containing a single-line YAML mapping with `trigger: test-robottelo` and any additional parameters.

**Q: Can I specify which tests to run?**
A: Yes, use the `pytest:` field with standard pytest options like `-k` for keyword filtering or direct test paths.

**Q: What if my PR fails automated tests?**
A: Review the test results, fix the issues, and re-trigger PRT by adding a new comment.

**Q: What does "No test results found" mean?**
A: The status alone does not identify the cause. Check the Jenkins console log for the reported
build number for errors in comment parsing, provisioning, package installation, or test startup
before changing the trigger and retrying.

**Q: Can I run PRT on specific environments?**
A: Yes, use environment variables via the `env:` field in your PRT comment.
