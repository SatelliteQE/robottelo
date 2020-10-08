import pytest
from fauxfactory import gen_string
from nailgun import entities

from robottelo.constants import DEFAULT_LOC


@pytest.fixture(scope='module')
def module_viewer_user(module_org):
    """Custom user with viewer role for tests validating visibility of entities or fields created
    by some other user. Created only when accessed, unlike `module_user`.
    """
    viewer_role = entities.Role().search(query={'search': 'name="Viewer"'})[0]
    default_loc_id = (
        entities.Location().search(query={'search': 'name="{}"'.format(DEFAULT_LOC)})[0].id
    )
    custom_password = gen_string('alphanumeric')
    custom_user = entities.User(
        admin=False,
        default_organization=module_org,
        location=[default_loc_id],
        organization=[module_org],
        role=[viewer_role],
        password=custom_password,
    ).create()
    custom_user.password = custom_password
    return custom_user
