import datetime
import glob
import os
from pathlib import Path
from shutil import copyfile
from tempfile import NamedTemporaryFile

import pytest
import xmltodict
from fauxfactory import gen_string

XUNIT_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S"
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

paths = [
    ["['testsuites']['testsuite']['properties']['property']"],
    [
        f"['testsuites']['testsuite']['testcase'][{i}]['properties']['property']"
        for i in range(dummy_test_count)
    ],
]


@pytest.fixture(scope="session")
def config():
    path = Path(__file__).parent
    conf_path = path / "../foreman"
    copyfile(str(conf_path / '../foreman/conftest.py'), f'{str(path)}/conftest.py')
    yield
    os.remove(f'{str(path)}/conftest.py')


@pytest.fixture(scope="session")
def exec_test(config):
    test_dir = str(Path(__file__).parent)
    report_file = f'report_{gen_string("alphanumeric")}.xml'
    with NamedTemporaryFile(dir=test_dir, mode='w', prefix='test_', suffix='.py') as f:
        f.seek(0)
        f.write(dummy_test)
        f.flush()
        pytest.main(['-n2', f'--junit-xml={report_file}', f'{f.name}::test_dummy'])
    yield report_file
    for logfile in glob.glob("robottelo*.log"):
        os.remove(logfile)
    try:
        os.remove(report_file)
    except OSError:
        # the file might not exist if the test fails prematurely
        pass


@pytest.mark.parametrize('paths', paths, ids=['testsuite', 'testcase'])
def test_junit_timestamps(exec_test, paths, request):
    """Asserts the 'start_time' property nodes existence in the junit-xml test report"""
    with open(exec_test, 'rb') as f:
        junit = xmltodict.parse(f)  # NOQA
    for path in paths:
        prop = eval(f"junit{path}")
        try:
            assert prop['@name'] == 'start_time'
        except KeyError as e:
            raise AssertionError(f'Missing property node: "start_time": {e}')
        try:
            datetime.datetime.strptime(prop['@value'], XUNIT_TIME_FORMAT)
        except ValueError as e:
            raise AssertionError(f'Unable to parse datetime for "start_time" property node: {e}')
