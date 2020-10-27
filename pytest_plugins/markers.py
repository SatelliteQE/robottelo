# Custom markers for robottelo tests


def pytest_configure(config):
    """Register custom markers to avoid warnings."""
    markers = [
        "deselect(reason=None): Mark test to be removed from collection.",
        "skip_if_open(issue): Skip test based on issue status.",
        "tier1: Tier 1 tests",  # CRUD tests
        "tier2: Tier 2 tests",  # Association tests
        "tier3: Tier 3 tests",  # Systems integration tests
        "tier4: Tier 4 tests",  # Long running tests
        "destructive: Destructive tests",
        "upgrade: Upgrade tests",
        "run_in_one_thread: Sequential tests",
    ]
    for marker in markers:
        config.addinivalue_line("markers", marker)
