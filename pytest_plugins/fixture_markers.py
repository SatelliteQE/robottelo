from inspect import getmembers
from inspect import isfunction

from robottelo.config import settings


def pytest_generate_tests(metafunc):
    if 'rhel_contenthost' in metafunc.fixturenames:
        rhel_parameters = [
            dict(workflow=settings.content_host.deploy_workflow, rhel_version=ver)
            for ver in settings.content_host.rhel_versions
        ]
        metafunc.parametrize(
            'rhel_contenthost',
            rhel_parameters,
            ids=[f'rhel{r["rhel_version"]}' for r in rhel_parameters],
            indirect=True,
        )


def pytest_configure(config):
    """Register markers related to testimony tokens"""
    for marker in ['content_host: Test uses a content host deployed by broker']:
        config.addinivalue_line("markers", marker)


def pytest_collection_modifyitems(session, items, config):
    from pytest_fixtures.core import contenthosts

    content_host_fixture_names = [m[0] for m in getmembers(contenthosts, isfunction)]
    for item in items:
        if set(item.fixturenames).intersection(set(content_host_fixture_names)):
            # TODO check param for indirect version parametrization
            item.add_marker('content_host')
