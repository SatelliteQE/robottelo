# Settings Fixtures
import pytest
from nailgun import entities


@pytest.fixture(scope="function")
def setting_update(request):
    """
    This fixture is used to create an object of the provided settings parameter that we use in
    each test case to update their attributes and once the test case gets completed it helps to
    restore their default value
    """
    setting_object = entities.Setting().search(query={'search': f'name={request.param}'})[0]
    default_setting_value = setting_object.value
    if default_setting_value is None:
        default_setting_value = ''
    yield setting_object
    setting_object.value = default_setting_value
    setting_object.update({'value'})
