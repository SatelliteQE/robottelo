import pytest
from fauxfactory import gen_string
from nailgun import entities


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
