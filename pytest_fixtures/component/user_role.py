from fauxfactory import gen_alphanumeric
import pytest


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
