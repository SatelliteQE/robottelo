import glob
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from fauxfactory import gen_string
import pytest


@pytest.fixture(scope='session', autouse=True)
def align_to_satellite():
    """Override align_to_satellite used in functional tests"""
    pass


@pytest.fixture
def dummy_test(request):
    """This should be indirectly parametrized to provide dynamic dummy_tests to exec_test"""
    return request.param


@pytest.fixture
def exec_test(request, dummy_test):
    """Create a temporary file with the string provided by dummy_test, and run it with pytest.main

    pytest arguments can be indirectly parametrized, and are handled as a string

    Writes and returns a junit-xml file

    """
    param_args = getattr(request, 'param', None)
    pytest_args = ['--capture=sys', '-q']
    if param_args:
        pytest_args.append(param_args)
    test_dir = str(Path(__file__).parent)
    report_file = f'report_{gen_string("alphanumeric")}.xml'
    pytest_args.append(f'--junit-xml={report_file}')
    with NamedTemporaryFile(dir=test_dir, mode='w', prefix='test_', suffix='.py') as f:
        f.seek(0)
        f.write(dummy_test['body'])
        f.flush()
        pytest_args.append(f'{f.name}::{dummy_test["name"]}')
        pytest.main(pytest_args)
    yield report_file
    for logfile in glob.glob('robottelo*.log'):
        os.remove(logfile)
    try:
        os.remove(report_file)
    except OSError:
        # the file might not exist if the test fails prematurely
        pass
