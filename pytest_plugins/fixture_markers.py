from inspect import getmembers, isfunction
import re

import pytest

from robottelo.config import settings
from robottelo.enums import NetworkType

TARGET_FIXTURES = [
    'rhel_contenthost',
    'rhel_contenthost_with_repos',
    'module_rhel_contenthost',
    'mod_content_hosts',
    'content_hosts',
    'module_provisioning_rhel_content',
    'capsule_provisioning_rhel_content',
    'module_sync_kickstart_content',
    'rex_contenthost',
    'rex_contenthosts',
]


def pytest_generate_tests(metafunc):
    content_host_fixture = ''.join([i for i in TARGET_FIXTURES if i in metafunc.fixturenames])
    if content_host_fixture in metafunc.fixturenames:
        function_marks = getattr(metafunc.function, 'pytestmark', [])
        no_containers = any(mark.name == 'no_containers' for mark in function_marks)
        # process eventual rhel_version_list markers
        matchers = [i.args for i in function_marks if i.name == 'rhel_ver_list']
        list_params = []
        for matcher in matchers:
            list_params.extend(
                [
                    setting_rhel_ver
                    for setting_rhel_ver in settings.supportability.content_hosts.rhel.versions
                    if str(setting_rhel_ver) in str(matcher)
                ]
            )
        # process eventual rhel_version_match markers
        matchers = [i.args for i in function_marks if i.name == 'rhel_ver_match']
        match_params = []
        # check if param matches format 'N-x'
        if matchers and len(matchers[0][0]) == 3 and matchers[0][0].startswith('N-'):
            # num of desired prior versions
            num_versions = int(matchers[0][0].split('-')[1])
            # grab major versions, excluding fips, from tail of supportability list
            filtered_versions = [
                setting_rhel_ver
                for setting_rhel_ver in settings.supportability.content_hosts.rhel.versions
                if 'fips' not in str(setting_rhel_ver)
            ][-(num_versions + 1) :]  # inclusive (+1) to collect N as well
            match_params.extend(filtered_versions)
        # match versions with existing regex markers
        else:
            for matcher in matchers:
                match_params.extend(
                    [
                        setting_rhel_ver
                        for setting_rhel_ver in settings.supportability.content_hosts.rhel.versions
                        if re.fullmatch(str(matcher[0]), str(setting_rhel_ver))
                    ]
                )
        rhel_params = []
        ids = []
        filtered_versions = set(list_params + match_params)
        # default to all supported versions if no filters were found
        for ver in filtered_versions or settings.supportability.content_hosts.rhel.versions:
            rhel_params.append(dict(rhel_version=ver, no_containers=no_containers))

        # Determine the default network type based on settings
        if settings.content_host.network_type == NetworkType.DUALSTACK:
            network_params = [NetworkType.IPV4, NetworkType.IPV6]
        else:  # rely on network_type setting to be either ipv4 or ipv6
            network_params = [settings.content_host.network_type]

        # Check for the network marker
        network_marker = metafunc.definition.get_closest_marker("network")

        # If network marker is present, validate its arguments and use it to filter network types
        if network_marker:
            marker_network_types = network_marker.args[0] if network_marker.args else network_params
            # Validate the network marker arguments
            for nt in marker_network_types:
                if nt not in [NetworkType.IPV4, NetworkType.IPV6]:
                    raise ValueError(
                        f"Invalid network type '{nt}' in network marker "
                        f"for test {metafunc.function.name}. "
                        f"Must be '{NetworkType.IPV4.value}' or '{NetworkType.IPV6.value}'."
                    )
            network_params = [nt for nt in marker_network_types if nt in network_params]
            # do not parametrize if no network types are common, test
            # should be skipped in pytest_collection_modifyitems

        # Check whether server could connect with client looking up settings.server.network_type
        if settings.server.network_type == NetworkType.IPV6:
            network_params = [
                nt for nt in network_params if nt in [NetworkType.IPV6, NetworkType.DUALSTACK]
            ]
        elif settings.server.network_type == NetworkType.IPV4:
            network_params = [
                nt for nt in network_params if nt in [NetworkType.IPV4, NetworkType.DUALSTACK]
            ]
        elif settings.server.network_type == NetworkType.DUALSTACK:
            network_params = [
                nt
                for nt in network_params
                if nt in [NetworkType.IPV4, NetworkType.IPV6, NetworkType.DUALSTACK]
            ]

        # Create combinations of rhel_params and network_params as dictionaries
        if rhel_params:
            rhel_params.sort(key=lambda r: str(r['rhel_version']))
            ids = [f'rhel{r["rhel_version"]}' for r in rhel_params]
            if network_params:
                rhel_params = [
                    {**rhel, 'network': net} for rhel in rhel_params for net in network_params
                ]
                ids = [f"rhel{param['rhel_version']}-{param['network']}" for param in rhel_params]

        if rhel_params:
            metafunc.parametrize(
                content_host_fixture,
                rhel_params,
                ids=ids,
                indirect=True,
            )

    # satellite-maintain capsule parametrization
    if 'sat_maintain' in metafunc.fixturenames:
        function_marks = getattr(metafunc.function, 'pytestmark', [])
        # Default fixture to run tests on - satellite
        hosts = ['satellite']
        for mark in function_marks:
            if mark.name == 'capsule_only':
                hosts = ['capsule']
            elif mark.name == 'include_capsule':
                hosts += ['capsule']
        hosts = ['satellite'] if settings.remotedb.server else hosts
        metafunc.parametrize(
            'sat_maintain',
            hosts,
            ids=hosts,
            indirect=True,
        )


def pytest_configure(config):
    """Register markers related to testimony tokens"""
    for marker in ['content_host: Test uses a content host deployed by broker']:
        config.addinivalue_line("markers", marker)


def pytest_collection_modifyitems(session, items, config):
    from pytest_fixtures.core import contenthosts

    def chost_rhelver(params):
        """Helper to retrive the rhel_version of a client from test params"""
        for param in params:
            if 'contenthost' in param:
                return params[param].get('rhel_version')
        return None

    content_host_fixture_names = [m[0] for m in getmembers(contenthosts, isfunction)]
    for item in items:
        if set(item.fixturenames).intersection(set(content_host_fixture_names)):
            # TODO check param for indirect version parametrization
            if hasattr(item, 'callspec'):
                client_property = ('ClientOS', str(chost_rhelver(item.callspec.params)))
            else:
                client_property = ('ClientOS', str(settings.content_host.default_rhel_version))
            item.user_properties.append(client_property)
            item.add_marker('content_host')

        if network_marker := item.get_closest_marker("network"):
            marker_network_types = network_marker.args[0] if network_marker.args else []
            # Skip the test if network_type setting is not set to ipv4 and network marker is set to ipv6
            if 'ipv6' in marker_network_types and settings.content_host.network_type not in [
                'ipv6',
                'dualstack',
            ]:
                item.add_marker(
                    pytest.mark.skip(reason=f"Skipping {item.name} due to network type mismatch")
                )
            # Skip the test if network_type setting is not set to ipv6 and network marker is set to ipv4
            if 'ipv4' in marker_network_types and settings.content_host.network_type not in [
                'ipv4',
                'dualstack',
            ]:
                item.add_marker(
                    pytest.mark.skip(reason=f"Skipping {item.name} due to network type mismatch")
                )


def pytest_addoption(parser):
    """Add CLI options related to Host-related mark collection"""
    parser.addoption(
        '--no-containers',
        action='store_true',
        help='Disable container hosts from being used in favor of VMs',
    )
