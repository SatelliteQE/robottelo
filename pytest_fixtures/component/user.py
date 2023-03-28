import pytest
from nailgun import entities


@pytest.fixture
def user_not_exists(request):
    """Remove a user if it exists. Return whether changes have been applied."""
    users = entities.User().search(query={'search': f'login={request.param}'})
    if users:
        users[0].delete()
        return True
    else:
        return False
