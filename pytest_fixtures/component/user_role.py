from fauxfactory import gen_alphanumeric
import pytest

from robottelo.constants import ROLES


class UserFactory:
    """Helper class for more complex operations with users that can be reused in fixtures."""

    @staticmethod
    def create_user(target_sat, **params):
        """Create and return a user object. Set the password if not specified.
        Args:
            target_sat: Satellite object
            params: parameters passed to the User object
        Returns:
             User object
        """
        params.setdefault('password', gen_alphanumeric())
        user = target_sat.api.User(**params).create()
        user.password = params['password']
        return user


@pytest.fixture(scope='session')
def viewer_role(session_target_sat):
    """Viewer role."""
    return session_target_sat.api.Role().search(query={'search': 'name="Viewer"'})[0]


@pytest.fixture(scope='session')
def expected_roles(expected_permissions):
    """Return built-in roles provided by the current Satellite features.

    Drop only roles whose plugin permissions are absent or whose foremanctl support
    is tracked as incomplete, matching the API permission expectations.
    """
    roles = ROLES.copy()
    unavailable_roles = set()
    if 'download_bootdisk' not in expected_permissions[None]:
        unavailable_roles.add('Boot disk access')
    if 'Template' not in expected_permissions:
        unavailable_roles.update({'Content Exporter', 'Content Importer'})
    if 'DiscoveryRule' not in expected_permissions:
        unavailable_roles.update({'Discovery Manager', 'Discovery Reader'})
    if 'ForemanOpenscap::ArfReport' not in expected_permissions:
        unavailable_roles.update({'Compliance manager', 'Compliance viewer', 'Create ARF report'})
    if 'ForemanVirtWhoConfigure::Config' not in expected_permissions:
        unavailable_roles.update({'Virt-who Manager', 'Virt-who Reporter', 'Virt-who Viewer'})
    if 'JobInvocation' not in expected_permissions:
        unavailable_roles.update({'Remote Execution Manager', 'Remote Execution User'})
    return [role for role in roles if role not in unavailable_roles]


@pytest.fixture(scope='class')
def class_user_password():
    """Generate a random password for a user, and capture it so a test has access to it"""
    return gen_alphanumeric()


@pytest.fixture
def function_role(target_sat):
    return target_sat.api.Role().create()


@pytest.fixture
def function_role_with_org(module_target_sat, module_org):
    return module_target_sat.api.Role(organization=[module_org]).create()


@pytest.fixture(scope='module')
def module_user(module_target_sat, module_org, module_location):
    return module_target_sat.api.User(
        organization=[module_org], location=[module_location]
    ).create()


@pytest.fixture(scope='module')
def default_viewer_role(module_target_sat, module_org, default_location, viewer_role):
    """Custom user with viewer role for tests validating visibility of entities or fields created
    by some other user. Created only when accessed, unlike `module_user`.
    """
    return UserFactory.create_user(
        target_sat=module_target_sat,
        admin=False,
        default_organization=module_org,
        location=[default_location],
        organization=[module_org],
        role=[viewer_role],
    )


@pytest.fixture(scope='module')
def module_user_viewer(module_target_sat, module_org, module_location, viewer_role):
    """Non-admin user with Viewer role."""
    return UserFactory.create_user(
        target_sat=module_target_sat,
        admin=False,
        location=[module_location],
        organization=[module_org],
        role=[viewer_role],
    )
