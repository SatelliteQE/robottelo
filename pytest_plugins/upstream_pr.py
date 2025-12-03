"""Pytest plugin for filtering tests based on upstream GitHub PR file changes.

This plugin allows filtering robottelo test collection by analyzing the files modified
in upstream GitHub pull requests (PRs) and mapping them to test components via configured rules.

Usage:
    pytest tests/foreman --upstream-pr foreman/12345,katello/6789

Configuration:
    Requires settings.github_repos configuration with repository mappings and file-to-component rules.
"""

import re

from github import Auth, Github
from github.GithubException import GithubException

from robottelo.config import settings
from robottelo.logging import collection_logger as logger


def match_file_to_rule(filename, rule):
    """File matching using regex patterns only.

    Args:
        filename: The filename to match against
        rule: Rule object with 'path' attribute containing the regex pattern

    Returns:
        bool: True if filename matches the rule pattern
    """
    path_pattern = rule.path

    try:
        return bool(re.search(path_pattern, filename))
    except re.error as e:
        logger.error(f"Invalid regex pattern '{path_pattern}': {e}")
        return False


def component_match(item, components, base_marker):
    """Return True if the test (`item`) has a marker matching one of the `components`.

    Requirements for a match:
    1. If `base_marker` is set, then `item` must have that marker.
    2. `item` must have a component marker matching one of the given `components`.

    Args:
        item: pytest test item to check
        components: set of component names to match against
        base_marker: optional base marker that must be present

    Returns:
        bool: True if item matches component and base marker requirements
    """
    # Check for base marker match, if one was specified
    if base_marker and not any(base_marker == marker.name for marker in item.iter_markers()):
        return False

    # Check for component marker matching any of the specified components
    return any(
        marker.name == 'component' and any(component in marker.args for component in components)
        for marker in item.iter_markers()
    )


def pytest_addoption(parser):
    """Add CLI option to specify upstream GitHub PRs.

    Adds --upstream-pr option for filtering tests based on files modified by upstream PRs.
    The option accepts comma-separated list of repository/PR_number pairs.

    Args:
        parser: pytest argument parser

    Example:
        pytest tests/foreman --upstream-pr foreman/12345,katello/6789
    """
    parser.addoption(
        "--upstream-pr",
        action="store",
        help=(
            "Comma-separated list of upstream PRs to filter test collection.\n"
            "Format: repo_key/pr_number (e.g., foreman/12345,katello/6789)\n"
            "Repository keys must be configured in settings.github_repos"
        ),
    )


def pytest_collection_modifyitems(session, items, config):
    """Filter tests based on upstream PRs.

    Process:
    1. Parse upstream PR specifications from command line
    2. Fetch modified files from each specified GitHub PR
    3. Map modified files to test components using configured rules
    4. Filter collected tests to include only those with matching components

    Args:
        session: pytest session object
        items: list of collected test items
        config: pytest configuration object

    Raises:
        ValueError: If PR format is invalid or repository key not found
        GithubException: If GitHub API access fails
    """
    # Parse upstream PR option
    if not (upstream_pr_option := config.getoption('upstream_pr')):
        return

    upstream_prs = [pr_info.strip() for pr_info in upstream_pr_option.split(',') if pr_info.strip()]
    if not upstream_prs:
        return

    components = set()
    gh_settings = settings.github_repos

    auth = None
    if token := gh_settings.get('token'):
        auth = Auth.Token(token)
    github_client = Github(auth=auth)

    for pr_info in upstream_prs:
        try:
            # Parse and validate the PR repo and id
            if '/' not in pr_info:
                raise ValueError(
                    f"Invalid PR format: '{pr_info}'. Expected format: repo_key/pr_number"
                )

            repo_key, pr_id_str = pr_info.split('/', 1)
            try:
                pr_id = int(pr_id_str)
            except ValueError as e:
                raise ValueError(f"Invalid PR number: '{pr_id_str}'. Must be an integer") from e

            # Validate repository configuration
            repo_config = gh_settings.repos.get(repo_key)
            if not repo_config:
                available_repos = ', '.join(gh_settings.repos.keys()) if gh_settings else 'none'
                raise ValueError(
                    f"Repository key '{repo_key}' not found in settings.github_repos. "
                    f"Available repositories: {available_repos}"
                )

            # Fetch PR data from GitHub
            logger.info(f"Fetching files modified in upstream PR {repo_key}/{pr_id}")
            repo_full_name = f"{repo_config.org}/{repo_config.repo}"
            try:
                github_repo = github_client.get_repo(repo_full_name)
                pr = github_repo.get_pull(pr_id)
                pr_filenames = {file.filename for file in pr.get_files()}

                # Add validation for PR state
                if pr.state != 'open':
                    logger.warning(f"PR {repo_key}/{pr_id} is {pr.state}, results may be outdated")

            except GithubException as e:
                if e.status == 404:
                    logger.error(
                        f"PR {repo_key}/{pr_id} not found. Check PR number and repository access."
                    )
                elif e.status == 403:
                    logger.error(
                        "GitHub API rate limit or permission issue. Consider setting TOKEN to a GitHub token."
                    )
                else:
                    logger.error(f"GitHub API error for {repo_key}/{pr_id}: {e}")
                # Raise after logging error, do not continue with any other PRs
                raise

            # Map modified files to components using configured rules
            unprocessed_filenames = pr_filenames.copy()
            logger.debug(f'Upstream PR {repo_key}/{pr_id} modified files: {sorted(pr_filenames)}')
            if not repo_config.rules:
                logger.warning(
                    f"No rules configured for repository '{repo_key}', skipping component mapping"
                )
                continue

            for rule in repo_config.rules:
                if not hasattr(rule, 'path') or not hasattr(rule, 'component'):
                    logger.warning(
                        f"Invalid rule in {repo_key}: missing 'path' or 'component' attribute"
                    )
                    continue

                matched_filenames = {
                    filename
                    for filename in unprocessed_filenames
                    if match_file_to_rule(filename, rule)
                }
                if matched_filenames:
                    components.add(rule.component)
                    unprocessed_filenames.difference_update(matched_filenames)
                    logger.debug(
                        f"Rule '{rule.path}' matched {len(matched_filenames)} files, "
                        f"mapped to component '{rule.component}'"
                    )
            if unprocessed_filenames:
                logger.debug(
                    f"Unmatched files in {repo_key}/{pr_id}: {sorted(unprocessed_filenames)}"
                )

        except (ValueError, GithubException) as e:
            logger.error(f"Error processing PR {pr_info}: {e}")
            raise

    # Filter tests based on matched components
    if not components:
        logger.warning("No components matched from upstream PRs, all tests will be deselected")

    selected = []
    deselected = []
    base_marker = settings.github_repos.base_marker
    logger.info(f"Filtering tests based on components: {sorted(components)}")

    for item in items:
        if components and component_match(item, components, base_marker):
            logger.debug(f'Selected test {item.nodeid} (matches components: {components})')
            selected.append(item)
        else:
            logger.debug(f'Deselected test {item.nodeid} (no component match)')
            deselected.append(item)

    logger.info(f"Test filtering complete: {len(selected)} selected, {len(deselected)} deselected")

    # Apply the filtering
    if deselected:
        config.hook.pytest_deselected(items=deselected)
    items[:] = selected
