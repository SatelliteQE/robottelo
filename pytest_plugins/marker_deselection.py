import pytest

from robottelo.logging import collection_logger as logger


def pytest_addoption(parser):
    """Add options for pytest to collect tests than can run on SatLab infra"""
    options = [
        '--include-onprem-provisioning',
        '--include-libvirt',
        '--include-external-auth',
        '--include-vlan-networking',
    ]
    for opt in options:
        help_text = f'''Filter out tests depends on infra availability

                        Usage: `pytest tests/foreman {opt}`
                    '''
        parser.addoption(opt, action='store_true', default=False, help=help_text)


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(items, config):
    """
    Collects and modifies tests collection based on pytest option to deselect tests for new infra
    """
    include_onprem_provision = config.getoption('include_onprem_provisioning', False)
    include_libvirt = config.getoption('include_libvirt', False)
    include_eauth = config.getoption('include_external_auth', False)
    include_vlan = config.getoption('include_vlan_networking', False)
    selected = []
    deselected = []
    # Cloud Provisioning Test can be run on new pipeline
    for item in items:
        item_marks = [m.name for m in item.iter_markers()]
        # Include / Exclude On Premises Provisioning Tests
        if 'on_premises_provisioning' in item_marks:
            selected.append(item) if include_onprem_provision else deselected.append(item)
            continue
        # Include / Exclude External Libvirt based Tests
        if any(marker in item_marks for marker in ['libvirt_discovery', 'libvirt_content_host']):
            selected.append(item) if include_libvirt else deselected.append(item)
            continue
        # Include / Exclude External Auth based Tests
        if 'external_auth' in item_marks:
            selected.append(item) if include_eauth else deselected.append(item)
            continue
        # Include / Exclude VLAN networking based based Tests
        if 'vlan_networking' in item_marks:
            selected.append(item) if include_vlan else deselected.append(item)
            continue
        # This Plugin does not applies to this test
        selected.append(item)
    logger.debug(
        f'Selected {len(selected)} and deselected {len(deselected)} '
        'tests based on new infra markers.'
    )
    items[:] = selected or items
    config.hook.pytest_deselected(items=deselected)
