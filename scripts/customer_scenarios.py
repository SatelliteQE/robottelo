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
import testimony

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
def run(jira, paths=None):
    if jira:
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
