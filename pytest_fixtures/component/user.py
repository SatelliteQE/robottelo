import pytest


@pytest.fixture
def user_not_exists(request, target_sat):
    """Remove a user if it exists. Return whether changes have been applied."""
    if users := target_sat.api.User().search(query={'search': f'login={request.param}'}):
        users[0].delete()
    return bool(users)
