# Custom infra dependent markers for selection and deselection of tests


def pytest_configure(config):
    """Register custom markers to avoid warnings."""
    markers = [
        "on_premises_provisioning: Tests that runs on on_premises Providers",
        "libvirt_discovery: Tests depends on Libvirt Provider for discovery",
        "libvirt_content_host: Tests depends on Libvirt Provider for content hosts",
        "external_auth: External Authentication tests",
        "vlan_networking: Tests depends on static predefined vlan networking etc",
    ]
    for marker in markers:
        config.addinivalue_line("markers", marker)
