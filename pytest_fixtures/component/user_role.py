from fauxfactory import gen_alphanumeric, gen_string
import pytest


@pytest.fixture(scope='class')
def class_user_password():
    """Generate a random password for a user, and capture it so a test has access to it"""
    return gen_alphanumeric()


@pytest.fixture
def function_role(target_sat):
    return target_sat.api.Role().create()


@pytest.fixture(scope='module')
def module_user(module_target_sat, module_org, module_location):
    return module_target_sat.api.User(
        organization=[module_org], location=[module_location]
    ).create()


@pytest.fixture(scope='module')
def default_viewer_role(module_target_sat, module_org, default_location):
    """Custom user with viewer role for tests validating visibility of entities or fields created
    by some other user. Created only when accessed, unlike `module_user`.
    """
    viewer_role = module_target_sat.api.Role().search(query={'search': 'name="Viewer"'})[0]
    custom_password = gen_string('alphanumeric')
    custom_user = module_target_sat.api.User(
        admin=False,
        default_organization=module_org,
        location=[default_location],
        organization=[module_org],
        role=[viewer_role],
        password=custom_password,
    ).create()
    custom_user.password = custom_password
    return custom_user
