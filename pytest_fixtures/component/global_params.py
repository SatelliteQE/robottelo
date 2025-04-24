# Settings Fixtures
import pytest


@pytest.fixture
def multi_global_param_update(request, target_sat):
    """
    This fixture is used to alter multiple global parameters in one batch.
    """
    key_vals = request.param
    param_objects = []
    for key_val in key_vals:
        param, new_value = tuple(key_val.split('=')) if '=' in key_val else (key_val, None)
        existing_params = target_sat.api.CommonParameter().search(query={'search': f'name={param}'})
        if len(existing_params) > 0:
            assert len(existing_params) == 1, 'Unexpected number of parameters returned'
            param_object = existing_params[0]
            cleanup = False
            default_param_value = param_object.value
        else:
            param_object = target_sat.api.CommonParameter(name=param, value=new_value).create()
            cleanup = True
            default_param_value = new_value
        param_objects.append(
            {'object': param_object, 'default': default_param_value, 'cleanup': cleanup}
        )
    yield [item['object'] for item in param_objects]
    for item in param_objects:
        if item['cleanup']:
            item['object'].delete()
        else:
            item['object'].value = item['default']
            item['object'].update({'value'})
