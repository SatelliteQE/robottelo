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
            ids=[f'rhel_{r["rhel_version"]}' for r in rhel_parameters],
            indirect=True,
        )
