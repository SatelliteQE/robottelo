import pytest
from fauxfactory import gen_alphanumeric
from fauxfactory import gen_string
from nailgun import entities


@pytest.fixture(scope='class')
def class_user_password():
    """Generate a random password for a user, and capture it so a test has access to it"""
    return gen_alphanumeric()


@pytest.fixture
def function_role():
    return entities.Role().create()


@pytest.fixture(scope='module')
def module_user(module_org, module_location):
    return entities.User(organization=[module_org], location=[module_location]).create()


@pytest.fixture(scope='module')
def default_viewer_role(module_org, default_location):
    """Custom user with viewer role for tests validating visibility of entities or fields created
    by some other user. Created only when accessed, unlike `module_user`.
    """
    viewer_role = entities.Role().search(query={'search': 'name="Viewer"'})[0]
    custom_password = gen_string('alphanumeric')
    custom_user = entities.User(
        admin=False,
        default_organization=module_org,
        location=[default_location],
        organization=[module_org],
        role=[viewer_role],
        password=custom_password,
    ).create()
    custom_user.password = custom_password
    return custom_user
