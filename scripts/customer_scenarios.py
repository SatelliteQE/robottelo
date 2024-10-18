#!/usr/bin/env python
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "click",
#     "requests",
#     "testimony",
# ]
# ///
from functools import cache

import click
import requests
import testimony

from robottelo.config import settings
from robottelo.utils.issue_handlers.jira import get_data_jira


@click.group()
def main():
    pass


def make_path_list(path_list):
    targets = ['tests/foreman', 'tests/upgrades']
    if path_list:
        paths = path_list.split(',')
        paths = [path for path in paths if any(target in path for target in targets)]
        return set(paths)
    return targets


def get_bz_data(paths):
    testcases = testimony.get_testcases(paths)
    result = {}
    for path, tests in testcases.items():
        path_result = []
        for test in tests:
            test_dict = test.to_dict()
            test_data = {**test_dict['tokens'], **test_dict['invalid-tokens']}
            lowered_test_data = {name.lower(): val for name, val in test_data.items()}
            if 'bz' in lowered_test_data and (
                'customerscenario' not in lowered_test_data
                or lowered_test_data['customerscenario'] == 'false'
            ):
                path_result.append([test.name, lowered_test_data['bz']])
        if path_result:
            result[path] = path_result
    return result


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


@cache
def get_response(bzs):
    bz_fields = [
        'id',
        'summary',
        'status',
        'resolution',
        'cf_last_closed',
        'external_bugs',
    ]
    bz_url = settings.bugzilla.url
    bz_key = settings.bugzilla.api_key
    response = requests.get(
        f'{bz_url}/rest/bug',
        params={
            'id': bzs,
            'include_fields': ','.join(bz_fields),
        },
        headers={"Authorization": f"Bearer {bz_key}"},
    )
    assert response.status_code == 200, 'BZ query unsuccessful'
    assert response.json().get('error') is not True, response.json().get('message')
    return response.json().get('bugs')


def query_bz(data):
    output = []
    with click.progressbar(data.items()) as bar:
        for path, tests in bar:
            for test in tests:
                bugs = get_response(test[1])
                for bug in bugs:
                    if 'external_bugs' in bug and len(bug['external_bugs']) > 1:
                        customer_cases = [
                            case
                            for case in bug['external_bugs']
                            if 'Red Hat Customer Portal' in case['type']['description']
                        ]
                        if len(customer_cases) > 0:
                            output.append(f'{path} {test}')
    return set(output)


def query_jira(data):
    """Returns the list of path and test name for missing customerscenario token

    Arguments:
         data {dict} -- The list of test modules and tests without customerscenario tags
    """
    output = []
    sfdc_counter_field = 'customfield_12313440'
    with click.progressbar(data.items()) as bar:
        for path, tests in bar:
            for test in tests:
                jira_data = get_data_jira(test[1], jira_fields=[sfdc_counter_field])
                for data in jira_data:
                    customer_cases = int(float(data[sfdc_counter_field]))
                    if customer_cases and customer_cases >= 1:
                        output.append(f'{path} {test}')
                        break
    return set(output)


@main.command()
@click.option('--jira', is_flag=True, help='Run the customer scripting for Jira')
@click.option('--bz', is_flag=True, help='Run the customer scripting for BZ')
def run(jira, bz, paths=None):
    if jira:
        path_list = make_path_list(paths)
        values = get_tests_path_without_customer_tag(path_list)
        results = query_jira(values)
    elif bz:
        path_list = make_path_list(paths)
        values = get_bz_data(path_list)
        results = query_bz(values)
    else:
        raise UserWarning('Choose either `--jira` or `--bz` option')

    if len(results) == 0:
        click.echo('No action needed for customerscenario tags')
    else:
        click.echo('The following tests need customerscenario tags:')
        for result in results:
            click.echo(result)


if __name__ == '__main__':
    run()
