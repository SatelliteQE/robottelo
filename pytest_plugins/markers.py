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
        "build_sanity: Fast, basic tests that confirm build is ready for full test suite",
    ]
    markers.extend(module_markers())
    for marker in markers:
        config.addinivalue_line("markers", marker)


def module_markers():
    """Register custom markers for each module"""
    return [
        "host_create: Marks host creation CLI tests",
        "host_update: Marks host update CLI tests",
        "host_parameter: Marks host parameter CLI tests",
        "katello_host_tools: Marks host CLI tests where katello host tools is installed on client",
        "host_subscription: Marks host subscription CLI tests",
    ]
