import datetime

import pytest
import xmltodict

XUNIT_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S'
dummy_test_count = 2
dummy_test = f'''import pytest

@pytest.mark.parametrize('param', list(range(0, {dummy_test_count})))
def test_dummy(param):
    """A dummy test used by test_junit_timestamps.
    Not to be run as a standalone test
    """
    print(f'running test {{param}}')
    pass
'''

property_paths = [
    ["['testsuites']['testsuite']['properties']['property']"],
    [
        f"['testsuites']['testsuite']['testcase'][{i}]['properties']['property']"
        for i in range(dummy_test_count)
    ],
]


@pytest.mark.parametrize('property_level', property_paths, ids=['testsuite', 'testcase'])
@pytest.mark.parametrize('exec_test', ['-n2', '-n0'], ids=['xdist', 'non_xdist'], indirect=True)
@pytest.mark.parametrize('dummy_test', [dummy_test], ids=['dummy_test'], indirect=True)
def test_junit_timestamps(exec_test, property_level):
    """Asserts the 'start_time' property nodes existence in the junit-xml test report"""
    with open(exec_test, 'rb') as f:
        junit = xmltodict.parse(f)  # NOQA
    for path in property_level:
        prop = eval(f'junit{path}')
        if not isinstance(prop, list):
            prop = [prop]
        try:
            assert 'start_time' in [p['@name'] for p in prop]
        except KeyError as e:
            raise AssertionError(f'Missing property node: "start_time": {e}')
        try:
            for p in prop:
                if p['@name'] == 'start_time':
                    datetime.datetime.strptime(p['@value'], XUNIT_TIME_FORMAT)
        except ValueError as e:
            raise AssertionError(f'Unable to parse datetime for "start_time" property node: {e}')
