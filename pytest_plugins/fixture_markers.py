import re
from inspect import getmembers
from inspect import isfunction

from robottelo.config import settings


def pytest_generate_tests(metafunc):
    if 'rhel_contenthost' in metafunc.fixturenames:
        function_marks = getattr(metafunc.function, 'pytestmark', [])
        # process eventual rhel_version_list markers
        matchers = [i.args for i in function_marks if i.name == 'rhel_ver_list']
        list_params = []
        for matcher in matchers:
            list_params.extend(
                [
                    setting_rhel_ver
                    for setting_rhel_ver in settings.content_host.rhel_versions
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
                    for setting_rhel_ver in settings.content_host.rhel_versions
                    if re.fullmatch(str(matcher[0]), str(setting_rhel_ver))
                ]
            )
        rhel_params = []
        filtered_versions = set(list_params + match_params)
        for ver, data in settings.content_host.rhel_versions.items():
            if ver in (filtered_versions or settings.content_host.rhel_versions):
                # prefer version-specific deploy workflow before using the default one
                workflow = data.get('deploy_workflow', settings.content_host.deploy_workflow)
                rhel_params.append(dict(workflow=workflow, rhel_version=ver))
        if rhel_params:
            metafunc.parametrize(
                'rhel_contenthost',
                rhel_params,
                ids=[f'rhel{r["rhel_version"]}' for r in rhel_params],
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
