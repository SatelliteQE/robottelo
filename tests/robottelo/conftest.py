def pytest_configure(config):
    """Register custom markers to avoid warnings."""
    markers = [
        "stubbed: Tests that are not automates yet.",
        "deselect(reason=None): Mark test to be removed from collection.",
        "tier1: CRUD tests",
        "tier2: Association tests",
        "tier3: Systems integration tests",
        "tier4: Long running tests",
        "destructive: Destructive tests",
        "upgrade: Upgrade tests",
        "run_in_one_thread: Sequential tests",
    ]
    for marker in markers:
        config.addinivalue_line("markers", marker)
