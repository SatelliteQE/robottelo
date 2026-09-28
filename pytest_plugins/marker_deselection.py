import pytest

from robottelo.config import settings
from robottelo.enums import InstallMethod
from robottelo.logging import collection_logger as logger


def pytest_addoption(parser):
    """Add options for pytest to collect tests than can run on SatLab infra"""
    infra_options = [
        '--include-onprem-provisioning',
        '--include-ipv6-provisioning',
        '--include-libvirt',
        '--include-external-auth',
        '--include-vlan-networking',
    ]
    for opt in infra_options:
        help_text = f'''Filter out tests depends on infra availability

                        Usage: `pytest tests/foreman {opt}`
                    '''
        parser.addoption(opt, action='store_true', default=False, help=help_text)


def _install_method_for_collection():
    """Resolve install method from server settings for test collection.

    Uses ``server.install_method`` from conf/server.yaml (or
    ``ROBOTTELO_SERVER__INSTALL_METHOD``). When set to ``auto``, falls back to
    ``server.deploy_arguments.deploy_container``.
    """
    install_method = settings.server.get('install_method', InstallMethod.AUTO)
    if install_method != InstallMethod.AUTO:
        return InstallMethod(install_method)
    if settings.server.deploy_arguments.get('deploy_container'):
        return InstallMethod.FOREMANCTL
    return None


INCOMPATIBLE_MARKERS = {
    InstallMethod.FOREMANCTL: 'foreman_installer',
    InstallMethod.INSTALLER: 'foremanctl',
}
DEPLOYMENT_MARKERS = INCOMPATIBLE_MARKERS.values()


def _markexpr_selects_marker(markexpr, marker_name):
    if marker_name not in markexpr:
        return False
    return f'not{marker_name}' not in markexpr.replace(' ', '')


def _bypass_install_method_filter(config):
    markexpr = config.option.markexpr
    if not markexpr:
        return False
    return any(_markexpr_selects_marker(markexpr, marker) for marker in DEPLOYMENT_MARKERS)


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(items, config):
    """
    Collects and modifies tests collection based on pytest option to deselect tests for new infra
    """
    include_onprem_provision = config.getoption('include_onprem_provisioning', False)
    include_ipv6_provisioning = config.getoption('include_ipv6_provisioning', False)
    install_method = _install_method_for_collection()
    bypass = _bypass_install_method_filter(config)
    incompatible_marker = None if bypass else INCOMPATIBLE_MARKERS.get(install_method)
    if install_method and bypass and INCOMPATIBLE_MARKERS.get(install_method):
        logger.info(
            'Skipping install method deselection due to manual marker selection '
            f'(install method: {install_method.value}, markexpr: {config.option.markexpr})'
        )

    selected = []
    deselected = []
    for item in items:
        item_marks = [mark.name for mark in item.iter_markers()]

        if incompatible_marker and incompatible_marker in item_marks:
            logger.info(
                f'Deselected test {item.nodeid} due to install method '
                f'{install_method.value} (marker: {incompatible_marker})'
            )
            deselected.append(item)
            continue
        if 'on_premises_provisioning' in item_marks:
            selected.append(item) if include_onprem_provision else deselected.append(item)
            continue
        if 'ipv6_provisioning' in item_marks:
            selected.append(item) if include_ipv6_provisioning else deselected.append(item)
            continue
        selected.append(item)
    logger.debug(
        f'Selected {len(selected)} and deselected {len(deselected)} '
        'tests based on auto un-collectable markers and pytest options.'
    )
    items[:] = selected
    config.hook.pytest_deselected(items=deselected)
