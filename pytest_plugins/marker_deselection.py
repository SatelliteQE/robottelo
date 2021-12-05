import pytest

from robottelo.logging import collection_logger as logger


non_satCI_components = ['Virt-whoConfigurePlugin']


def pytest_addoption(parser):
    """Add options for pytest to collect tests than can run on SatLab infra"""
    infra_options = [
        '--include-onprem-provisioning',
        '--include-libvirt',
        '--include-external-auth',
        '--include-vlan-networking',
    ]
    for opt in infra_options:
        help_text = f'''Filter out tests depends on infra availability

                        Usage: `pytest tests/foreman {opt}`
                    '''
        parser.addoption(opt, action='store_true', default=False, help=help_text)

    option = '--include-non-satci-tests'
    help_text = f'''Include auto uncollected non SatCI tests

        Usage: `pytest tests/foreman {option} Virt-whoConfigurePlugin,SomthingComponent`
        '''
    parser.addoption(option, default='', help=help_text)


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(items, config):
    """
    Collects and modifies tests collection based on pytest option to deselect tests for new infra
    """
    include_onprem_provision = config.getoption('include_onprem_provisioning', False)
    include_libvirt = config.getoption('include_libvirt', False)
    include_eauth = config.getoption('include_external_auth', False)
    include_vlan = config.getoption('include_vlan_networking', False)
    include_non_satci_tests = config.getvalue('include_non_satci_tests').split(',')

    selected = []
    deselected = []
    # Cloud Provisioning Test can be run on new pipeline
    for item in items:
        # Include/Exclude tests those are not part of SatQE CI
        item_component = item.get_closest_marker('component')
        if item_component and (item_component.args[0] in non_satCI_components):
            if item_component.args[0] in include_non_satci_tests:
                selected.append(item)
            else:
                deselected.append(item)
            continue

        item_marks = [m.name for m in item.iter_markers()]
        # Include / Exclude On Premises Provisioning Tests
        if 'on_premises_provisioning' in item_marks:
            selected.append(item) if include_onprem_provision else deselected.append(item)
            continue
        # Include / Exclude External Libvirt based Tests
        if 'libvirt_discovery' in item_marks:
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
        'tests based on auto un-collectable markers and pytest options.'
    )
    items[:] = selected or items
    config.hook.pytest_deselected(items=deselected)
