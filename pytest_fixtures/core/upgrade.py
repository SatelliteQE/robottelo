import pytest


@pytest.fixture(scope="function")
def dependent_scenario_name(request):
    """
    This fixture is used to collect the depend test case name.
    """
    depend_test_name = [
        mark.kwargs['depend_on'].__name__
        for mark in request.node.own_markers
        if 'depend_on' in mark.kwargs
    ][0]
    yield depend_test_name
