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
        "tier5: Tier 5 tests",  # Deprecated component tests
        "destructive: Destructive tests",
        "upgrade: Upgrade tests",
        "e2e: End to end tests",
        "pit_server: PIT server scenario tests",
        "pit_client: PIT client scenario tests",
        "run_in_one_thread: Sequential tests",
        "build_sanity: Fast, basic tests that confirm build is ready for full test suite",
        "rhel_ver_list: Filter rhel_contenthost versions by list",
        "rhel_ver_match: Filter rhel_contenthost versions by regexp",
        "no_containers: Disable container hosts from being used in favor of VMs",
        "include_capsule: For satellite-maintain tests to run on Satellite and Capsule both",
        "capsule_only: For satellite-maintain tests to run only on Capsules",
    ]
    markers.extend(module_markers())
    for marker in markers:
        config.addinivalue_line("markers", marker)


def module_markers():
    """Register custom markers for each module"""
    return [
        "cli_host_create: Marks host creation CLI tests",
        "cli_host_update: Marks host update CLI tests",
        "cli_host_parameter: Marks host parameter CLI tests",
        "cli_katello_host_tools: Marks host CLI tests with katello host tools installed on client",
        "cli_host_subscription: Marks host subscription CLI tests",
        "cli_puppet_enabled: Marks CLI host tests with enabled puppet",
    ]
