# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "click",
# ]
# ///
from pathlib import Path
import re

import click

from robottelo.config import settings
from robottelo.constants import JIRA_COMMON_FIELDS
from robottelo.utils.issue_handlers.jira import get_data_jira, jira_cache

blocked_by_regex = re.compile(
    # To match :BlockedBy: SAT-32932
    r'\s*:BlockedBy:\s*(?P<blocked_by>.*\S*)',
    re.IGNORECASE,
)

verifies_regex = re.compile(
    # To match :Verifies: SAT-32932
    r'\s*:Verifies:\s*(?P<verifies>.*\S*)',
    re.IGNORECASE,
)


@click.command()
@click.argument('tests_dir', type=click.Path(exists=True, file_okay=False))
@click.option('--fresh', is_flag=True, help='Ignore existing cache and fetch all issue data.')
def populate_jira_cache(tests_dir, fresh):
    """Scan test files for Jira issues and populate the Jira cache."""

    def extract_jira_issues_from_file(file_path):
        """Extract Jira issue IDs from a Python file's docstrings."""
        content = Path(file_path).read_text()

        issues = []
        blocked_by = blocked_by_regex.findall(content)
        verifies = verifies_regex.findall(content)
        if blocked_by:
            issues.extend(issue.strip() for match in blocked_by for issue in match.split(','))
        if verifies:
            issues.extend(issue.strip() for match in verifies for issue in match.split(','))
        return issues

    def scan_test_directory(directory_path):
        """Recursively scan directory for Python files and extract Jira issues."""
        all_issues = set()

        directory = Path(directory_path)
        for file_path in directory.glob('**/test_*.py'):
            issues = extract_jira_issues_from_file(file_path)
            all_issues.update(issues)
        return all_issues

    click.echo(f"Scanning {tests_dir} for Jira issues...")
    issues = scan_test_directory(tests_dir)

    if not issues:
        click.echo("No Jira issues found in test files")
        return

    click.echo(f"Found {len(issues)} unique Jira issues")

    if fresh:
        click.echo("Fresh mode enabled. Fetching all issues regardless of cache status...")
        new_issues = issues
    else:
        # Check which issues are already in cache
        cached_issues = jira_cache.get_many(issues)
        cached_issues = {k for k, v in cached_issues.items() if v is not None}

        new_issues = issues - cached_issues
        if not new_issues:
            click.echo("All issues already in cache")
            return

    click.echo(f"Fetching data for {len(new_issues)} issues...")
    jira_fields_with_sfdc = JIRA_COMMON_FIELDS + [settings.jira.sfdc_counter_field]
    jira_data = get_data_jira(list(new_issues), jira_fields=jira_fields_with_sfdc)

    # Update cache with new data
    for issue in jira_data:
        jira_cache.update(issue['key'], issue)

    jira_cache.save()
    click.echo(f"Cache updated with {len(jira_data)} issues")


if __name__ == '__main__':
    populate_jira_cache()
