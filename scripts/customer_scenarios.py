#!/usr/bin/env python
from functools import cache

import click
import requests
import testimony

from robottelo.config import settings


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
            if 'bz' in test_data and (
                'customerscenario' not in test_data or test_data['customerscenario'] == 'false'
            ):
                path_result.append([test.name, test_data['bz']])
        if path_result:
            result[path] = path_result
    return result


def get_tests_path_without_customer_tag(paths):
    testcases = testimony.get_testcases(paths)
    result = {}
    for path, tests in testcases.items():
        path_result = []
        for test in tests:
            test_dict = test.to_dict()
            test_data = {**test_dict['tokens'], **test_dict['invalid-tokens']}
            if 'verifies' in test_data and (
                'customerscenario' not in test_data or test_data['customerscenario'] == 'false'
            ):
                path_result.append([test.name, test_data['verifies']])
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


def get_cached_single_jira_details(jira):
    from robottelo.utils.issue_handlers.jira import get_jira_issue

    return get_jira_issue(jira)


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
    output = []
    with click.progressbar(data.items()) as bar:
        for path, tests in bar:
            for test in tests:
                jira_data = get_cached_single_jira_details(test[1])
                customer_cases = int(
                    float(jira_data['issues'][0]['fields']['customfield_12313440'])
                )
                if customer_cases and customer_cases >= 1:
                    output.append(f'{path} {test}')
    return set(output)


# @main.command()
# def run(paths=None):
#     path_list = make_path_list(paths)
#     values = get_bz_data(path_list)
#     results = query_bz(values)
#     if len(results) == 0:
#         click.echo('No action needed for customerscenario tags')
#     else:
#         click.echo('The following tests need customerscenario tags:')
#         for result in results:
#             click.echo(result)


@main.command()
def run(paths=None):
    path_list = make_path_list(paths)
    values = get_tests_path_without_customer_tag(path_list)
    results = query_jira(values)
    if len(results) == 0:
        click.echo('No action needed for customerscenario tags')
    else:
        click.echo('The following tests need customerscenario tags:')
        for result in results:
            click.echo(result)


if __name__ == '__main__':
    run()
