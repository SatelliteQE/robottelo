# Settings Fixtures
import pytest


@pytest.fixture()
def setting_update(request, target_sat):
    """
    This fixture is used to create an object of the provided settings parameter that we use in
    each test case to update their attributes and once the test case gets completed it helps to
    restore their default value
    """
    key_val = request.param
    setting, new_value = tuple(key_val.split('=')) if '=' in key_val else (key_val, None)
    setting_object = target_sat.api.Setting().search(query={'search': f'name={setting}'})[0]
    default_setting_value = '' if setting_object.value is None else setting_object.value
    if new_value is not None:
        setting_object.value = new_value
        setting_object.update({'value'})
    yield setting_object
    setting_object.value = default_setting_value
    setting_object.update({'value'})
