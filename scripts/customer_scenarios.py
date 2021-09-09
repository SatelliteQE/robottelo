#!/usr/bin/env python
import os

import click
import requests
import testimony

from robottelo.config import settings


@click.group()
def main():
    pass


def make_path_list(path_list):
    paths = path_list.split(",")
    paths = [path for path in paths if 'tests/foreman' in path]
    return set(paths)


def get_bz_data(paths):
    testcases = testimony.get_testcases(paths)
    result = {}
    for path, tests in testcases.items():
        path_result = []
        for test in tests:
            test_dict = test.to_dict()
            test_data = {**test_dict['tokens'], **test_dict['invalid-tokens']}
            if 'bz' in test_data.keys():
                if (
                    'customerscenario' not in test_data.keys()
                    or test_data['customerscenario'] == 'false'
                ):
                    path_result.append([test.name, test_data['bz']])
        if path_result:
            result[path] = path_result
    return result


def query_bz(data):
    bz_fields = [
        "id",
        "summary",
        "status",
        "resolution",
        "cf_last_closed",
        "flags",
        "external_bugs",
    ]
    bz_url = "https://bugzilla.redhat.com"
    bz_key = settings.bugzilla.api_key
    click.echo(len(bz_key))
    # test = os.environ["bz_key"]
    click.echo(len(os.environ["ROBOTTELO_BUGZILLA__API_KEY"]))
    output = []
    for path, tests in data.items():
        for test in tests:
            response = requests.get(
                f"{bz_url}/rest/bug",
                params={
                    "id": ",".join(set(test[1])),
                    "api_key": bz_key,
                    "include_fields": ",".join(bz_fields),
                },
            )
            assert response.status_code == 200, "BZ query unsuccessful"
            bugs = response.json().get("bugs")
            for bug in bugs:
                bug["qe_test_coverage"] = None
                if "flags" in bug.keys():
                    coverage = [item for item in bug["flags"] if item["name"] == "qe_test_coverage"]
                    bug["qe_test_coverage"] = coverage[0]["status"] if coverage else None
                if "external_bugs" in bug.keys():
                    customer_cases = [
                        case
                        for case in bug["external_bugs"]
                        if case["type"]["description"] == "Red Hat Customer Portal"
                    ]
                    bug["customer_cases_count"] = len(customer_cases)
                if bug["customer_cases_count"] > 0:
                    output.append(f'{path} {test}')
    return set(output)


@main.command()
@click.option('--paths', nargs=1)
def run(paths):
    settings.configure()
    click.echo("Getting test data")
    path_list = make_path_list(paths)
    values = get_bz_data(path_list)
    click.echo(paths)
    click.echo("Querying bugzilla")
    results = query_bz(values)
    if len(results) == 0:
        click.echo("No action needed for customerscenario tags")
    else:
        click.echo("The following tests need customerscenario tags:")
        for result in results:
            click.echo(result)
        raise


if __name__ == "__main__":
    run()
