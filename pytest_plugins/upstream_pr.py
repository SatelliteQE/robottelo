from github import Github

from robottelo.config import settings
from robottelo.logging import collection_logger as logger


def rule_match(item, rules):
    """Return True if `item` has a marker matching one of the `rules`.

    In order for a rule to match:
    1. If `settings.github_repos.base_marker` exists, then `item` has a marker with the given value
    as its `name` attribute.
    2. `item` has a marker with the name given in `rule.marker`.
    3. If `rule.marker_arg` exists, then the item's marker must also have the given value in marker's
    `args` attribute.
    """
    base_marker = settings.github_repos.get('base_marker')
    return (
        not base_marker or any(base_marker == marker.name for marker in item.iter_markers())
    ) and any(
        rule.marker == marker.name
        and (not rule.get('marker_arg') or rule.get('marker_arg') in marker.args)
        for marker in item.iter_markers()
        for rule in rules
    )


def pytest_addoption(parser):
    """Add CLI option to specify upstream GitHub PRs.

    Add --upstream-pr option for filtering tests based on the files modified by upstream
    PRs.
    """
    parser.addoption(
        "--upstream-pr",
        help=(
            "Comma separated list of upstream PRs to filter test collection based on files modified in upstream.\n"
            "Usage: `pytest tests/foreman --upstream-pr foreman/10146`"
        ),
    )


def pytest_collection_modifyitems(session, items, config):
    """Filter tests based on upstream PRs.
    1. Get the list of modified files in the upstream PRs.
    2. Map each file to at most one marker.
    3. Filter the collected tests to include only those with matching markers.

    Note:
    If no rules were matched above, all tests will be deselected. Any unprocessed filenames
    (not matching any rules) are ignored.

    """
    upstream_prs = [
        pr_info for pr_info in (config.getoption('upstream_pr') or '').split(',') if pr_info != ''
    ]
    if not upstream_prs:
        return

    matched_rules = []
    for pr_info in upstream_prs:
        # Get all filenames modified by this PR
        repo_key, pr_id = pr_info.split('/')
        if not (repo_config := settings.github_repos.get(repo_key)):
            raise Exception(f"Key {repo_key} not found in settings file.")
        pr = Github().get_repo(f"{repo_config.org}/{repo_config.repo}").get_pull(int(pr_id))
        pr_filenames = {file.filename for commit in pr.get_commits() for file in commit.files}

        # Get a list of matching rules
        unprocessed_filenames = pr_filenames.copy()
        for rule in repo_config.rules:
            if matched_filenames := {
                filename for filename in unprocessed_filenames if filename.startswith(rule.path)
            }:
                matched_rules.append(rule)
                unprocessed_filenames.difference_update(matched_filenames)

    # If no rules were matched above, deselect all tests.
    # Any unprocessed filenames are ignored.
    selected = []
    deselected = []
    for item in items:
        if matched_rules:
            if rule_match(item, matched_rules):
                selected.append(item)
            else:
                logger.debug(f'Deselected test {item.nodeid} due to PR filter {upstream_prs}')
                deselected.append(item)
        else:
            logger.debug(f'Deselected test {item.nodeid} due to PR filter {upstream_prs}')
            deselected.append(item)

    config.hook.pytest_deselected(items=deselected)
    items[:] = selected
