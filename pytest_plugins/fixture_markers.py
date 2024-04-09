from inspect import getmembers, isfunction
import re

from robottelo.config import settings

TARGET_FIXTURES = [
    'rhel_contenthost',
    'module_rhel_contenthost',
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
        for matcher in matchers:
            match_params.extend(
                [
                    setting_rhel_ver
                    for setting_rhel_ver in settings.supportability.content_hosts.rhel.versions
                    if re.fullmatch(str(matcher[0]), str(setting_rhel_ver))
                ]
            )
        rhel_params = []
        filtered_versions = set(list_params + match_params)
        # default to all supported versions if no filters were found
        for ver in filtered_versions or settings.supportability.content_hosts.rhel.versions:
            rhel_params.append(dict(rhel_version=ver, no_containers=no_containers))
        if rhel_params:
            rhel_params.sort(key=lambda r: str(r['rhel_version']))
            metafunc.parametrize(
                content_host_fixture,
                rhel_params,
                ids=[f'rhel{r["rhel_version"]}' for r in rhel_params],
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


def pytest_addoption(parser):
    """Add CLI options related to Host-related mark collection"""
    parser.addoption(
        '--no-containers',
        action='store_true',
        help='Disable container hosts from being used in favor of VMs',
    )
