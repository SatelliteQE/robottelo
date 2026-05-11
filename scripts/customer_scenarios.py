#!/usr/bin/env python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "click",
#     "requests",
#     "testimony",
# ]
# ///

import click
from jira import JIRA
import testimony

from robottelo.config import settings
from robottelo.constants import JIRA_COMMON_FIELDS
from robottelo.utils.issue_handlers.jira import get_data_jira


@click.group()
def main():
    pass


def _jira_client():
    """Create a JIRA client with basic auth (email and api_key)."""
    return JIRA(
        server=settings.jira.url,
        basic_auth=(settings.jira.email, settings.jira.api_key),
    )


def make_path_list(path_list):
    targets = ['tests/foreman', 'tests/new_upgrades']
    if path_list:
        paths = path_list.split(',')
        paths = [path for path in paths if any(target in path for target in targets)]
        return set(paths)
    return targets


def get_tests_path_without_customer_tag(paths):
    """Returns the path and test name that does not have customerscenario token even
    though it has verifies token when necessary

    Arguments:
        paths {list} -- List of test modules paths
    """
    testcases = testimony.get_testcases(paths)
    result = {}
    for path, tests in testcases.items():
        path_result = []
        for test in tests:
            test_dict = test.to_dict()
            test_data = {**test_dict['tokens'], **test_dict['invalid-tokens']}
            # 1st level lowering should be good enough as `verifies` and `customerscenario`
            # tokens are at 1st level
            lowered_test_data = {name.lower(): val for name, val in test_data.items()}
            if 'verifies' in lowered_test_data and (
                'customerscenario' not in lowered_test_data
                or lowered_test_data['customerscenario'] == 'false'
            ):
                path_result.append([test.name, lowered_test_data['verifies']])
        if path_result:
            result[path] = path_result
    return result


def query_jira(data):
    """Returns the list of path and test name for missing customerscenario token

    Arguments:
         data {dict} -- The list of test modules and tests without customerscenario tags
    """
    output = []
    jira_fields_with_sfdc = JIRA_COMMON_FIELDS + [settings.jira.sfdc_counter_field]
    with click.progressbar(data.items()) as bar:
        for path, tests in bar:
            for test in tests:
                issues = [str(issue.strip()) for issue in test[1].split(',')]
                jira_data = get_data_jira(issues, jira_fields=jira_fields_with_sfdc)
                for data in jira_data:
                    customer_cases = int(data[settings.jira.sfdc_counter_field])
                    if customer_cases and customer_cases >= 1:
                        output.append(f'{path} {test}')
                        break
    return output


def create_jira_issue(comment):
    """Create jira issues based on missing customerscenario token

    Arguments:
         issue_data {dict} -- The list of test modules, tests without customerscenario tags and other jira fields.
    """
    jira = _jira_client()
    summary = "Add missing CustomerScenario tags for Robottelo tests"
    jql = f"summary ~ '{summary}' AND status != Closed ORDER BY created DESC"
    comment = 'The following tests need customerscenario tags:\n' + "\n".join(comment).strip()
    jira_fields_with_description = JIRA_COMMON_FIELDS + ['description']
    issues = jira.search_issues(jql_str=jql, fields=jira_fields_with_description, maxResults=1)
    if issues:
        issue = issues[0]
        if issue.fields.description.strip() != comment:
            click.echo(
                f'Found open issue {issue} for missing CustomerScenario tags. Updating the description.'
            )
            issue.update(fields={"description": comment})
        else:
            click.echo(
                f'Found open issue {issue} for missing CustomerScenario tags with same tests. Skipping update.'
            )
        return issue
    issue_data = {
        "project": settings.jira.project,
        "summary": summary,
        "issuetype": {"name": "Task"},
        "description": comment,
        "labels": ["qe-automation"],
        settings.jira.team_field: {"value": settings.jira.team},
        "components": [{"name": 'JPL - Tooling'}],
        settings.jira.story_points_field: 1,
        "security": {"name": settings.jira.comment_visibility},
    }
    click.echo('Creating JIRA issue for missing CustomerScenario tags')
    issue = jira.create_issue(issue_data)
    click.echo(f"Created {issue} JIRA issue for missing CustomerScenario tags")
    return issue


@main.command()
@click.option('--jira', is_flag=True, help='Run the customer scripting for Jira')
@click.option(
    '--create-jira', is_flag=True, help='Create jira issues based on missing customerscenario token'
)
def run(jira, create_jira, paths=None):
    if jira:
        path_list = make_path_list(paths)
        values = get_tests_path_without_customer_tag(path_list)
        results = sorted(set(query_jira(values)))

    if len(results) == 0:
        click.echo('No action needed for customerscenario tags')
    else:
        click.echo('The following tests need customerscenario tags:')
        for result in results:
            click.echo(result)
        if create_jira:
            create_jira_issue(results)


if __name__ == '__main__':
    run()
