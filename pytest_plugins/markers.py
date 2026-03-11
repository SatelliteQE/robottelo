# Custom markers for robottelo tests


def pytest_configure(config):
    """Register custom markers to avoid warnings."""
    markers = [
        "deselect(reason=None): Mark test to be removed from collection.",
        "destructive: Destructive tests",
        "upgrade: Upgrade tests",
        "e2e: End to end tests",
        "stream: Tests unique to stream builds; purged when robottelo is branched.",
        "pit_server: PIT server scenario tests",
        "pit_client: PIT client scenario tests",
        "client_release: For Client release testing; selected client side tests from OpenSCAP, pull provider, tracer etc.",
        "run_in_one_thread: Sequential tests",
        "build_sanity: Fast, basic tests that confirm build is ready for full test suite",
        "rhel_ver_list: Filter rhel_contenthost versions by list",
        "rhel_ver_match: Filter rhel_contenthost versions by regexp, or format 'N-#'",
        "no_containers: Disable container hosts from being used in favor of VMs",
        "include_capsule: For satellite-maintain tests to run on Satellite and Capsule both",
        "capsule_only: For satellite-maintain tests to run only on Capsules",
        "manifester: Tests that require manifester",
        "ldap: Tests related to ldap authentication",
        "no_compose : Skip the marked sanity test for nightly compose",
        "network: Restrict test to specific network environments",
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
