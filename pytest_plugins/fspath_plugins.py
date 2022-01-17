# File System related Collection Modification/Addition to test cases
import re


def pytest_collection_modifyitems(session, items, config):
    endpoint_regex = re.compile(
        # To match the endpoint in the fspath
        r'^.*/(?P<endpoint>\S*)/test_.*.py$',
        re.IGNORECASE,
    )
    for item in items:
        if item.nodeid.startswith('tests/robottelo/') or item.nodeid.startswith('tests/upgrades/'):
            continue

        endpoint = endpoint_regex.findall(item.location[0])[0]
        item.user_properties.append(('endpoint', endpoint))
