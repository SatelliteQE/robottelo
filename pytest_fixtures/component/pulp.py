"""Fixtures and helpers for Pulp-related tests

:Requirement: Pulp

:CaseAutomation: Automated

:CaseComponent: Pulp

:Team: Artemis

"""

from box import Box
from fauxfactory import gen_string
import pytest

from robottelo import constants
from robottelo.config import settings


def _setup_prn_content(sat, manifest, test_name=None):
    """Helper to set up content entities to properly test pulp HREF to PRN mapping.

    Creates:
        1. Organization with manifest uploaded.
        2. Product with multiple repository types.
        3. Yum repositories (with streams and srpms).
        4. Red Hat repository (rhsclient10).
        5. File repository.
        6. Docker repository with manifest list.
        7. Ansible Collection repository.
        8. CV with all repositories, LCE, including publish and promote.
        9. Alternate Content Sources (yum and file).

    Args:
        sat: Satellite instance
        manifest: SCA manifest object with .content attribute

    Returns:
        Box containing created entities (sat, org, product, repositories, etc.)
    """
    # Create an Organization and upload manifest
    org = sat.api.Organization(
        name=f'{test_name}_{gen_string("alpha")}' if test_name else gen_string('alpha')
    ).create()
    sat.upload_manifest(org.id, manifest.content)

    # Create a Product for custom repos
    product = sat.api.Product(
        organization=org,
        name=f'{test_name}_{gen_string("alpha")}' if test_name else gen_string('alpha'),
    ).create()

    # Create and sync yum repository with streams
    yum_repository = sat.api.Repository(
        product=product,
        url=settings.repos.module_stream_0.url,
        content_type='yum',
        name=f'{test_name}_{gen_string("alpha")}' if test_name else gen_string('alpha'),
    ).create()
    yum_repository.sync()

    # Create and sync yum repository with srpms
    srpm_repository = sat.api.Repository(
        product=product,
        url=constants.repos.FAKE_YUM_SRPM_REPO,
        content_type='yum',
        name=f'{test_name}_{gen_string("alpha")}' if test_name else gen_string('alpha'),
    ).create()
    srpm_repository.sync()

    # Create ULN repository with ULN remote
    uln_repository = sat.api.Repository(
        product=product,
        url='uln://fake.unbreakable.linux.netw.org',
        content_type='yum',
        upstream_username=gen_string('alpha'),
        upstream_password=gen_string('alpha'),
        name=f'{test_name}_{gen_string("alpha")}' if test_name else gen_string('alpha'),
    ).create()

    # Enable and sync Red Hat repository
    rh_repo_id = sat.api_factory.enable_rhrepo_and_fetchid(
        basearch=constants.DEFAULT_ARCHITECTURE,
        org_id=org.id,
        product=constants.PRDS['rhel10'],
        repo=constants.REPOS['rhsclient10']['name'],
        reposet=constants.REPOSET['rhsclient10'],
        releasever=constants.REPOS['rhsclient10']['releasever'],
    )
    rh_repo = sat.api.Repository(id=rh_repo_id).read()
    rh_repo.sync()

    # Create and sync file repository
    file_repository = sat.api.Repository(
        product=product,
        content_type='file',
        url=settings.repos.file_type_repo.url,
        name=f'{test_name}_{gen_string("alpha")}' if test_name else gen_string('alpha'),
    ).create()
    file_repository.sync()

    # Create and sync docker repository
    docker_repository = sat.api.Repository(
        product=product,
        content_type='docker',
        docker_upstream_name=settings.container.upstream_name,
        url=settings.container.registry_hub,
        name=f'{test_name}_{gen_string("alpha")}' if test_name else gen_string('alpha'),
    ).create()
    docker_repository.sync()

    # Create and sync Ansible Collection repository
    ac_repository = sat.api.Repository(
        product=product,
        content_type='ansible_collection',
        ansible_collection_requirements='{collections: [{ name: theforeman.foreman, version: "2.1.0"}]}',
        url=constants.repos.ANSIBLE_GALAXY,
        name=f'{test_name}_{gen_string("alpha")}' if test_name else gen_string('alpha'),
    ).create()
    ac_repository.sync()

    # Create, publish and promote content view with all repositories
    repos = [
        yum_repository,
        srpm_repository,
        uln_repository,
        rh_repo,
        file_repository,
        docker_repository,
        ac_repository,
    ]
    cv = sat.api.ContentView(organization=org, repository=repos).create()
    lce = sat.api.LifecycleEnvironment(organization=org).create()

    cv.publish()
    cvv = cv.read().version[0].read()
    cvv.promote(data={'environment_ids': lce.id, 'force': False})

    # Create ACS of each content type
    ACSes = []
    for content_type in ['yum', 'file']:
        acs = sat.api.AlternateContentSource(
            alternate_content_source_type='custom',
            content_type=content_type,
            base_url=constants.repos.PULP_FIXTURE_ROOT,
            subpaths=constants.repos.PULP_SUBPATHS_COMBINED[content_type],
            smart_proxy_ids=[sat.nailgun_capsule.id],
            verify_ssl=False,
            name=f'{test_name}_{gen_string("alpha")}' if test_name else gen_string('alpha'),
        ).create()
        ACSes.append(acs)

    return Box(
        {
            'target_sat': sat,
            'org': org,
            'product': product,
            'yum_repo': yum_repository,
            'srpm_repo': srpm_repository,
            'uln_repo': uln_repository,
            'rh_repo': rh_repo,
            'file_repo': file_repository,
            'docker_repo': docker_repository,
            'ac_repo': ac_repository,
            'cv': cv,
            'lce': lce,
            'ACSes': ACSes,
        }
    )


@pytest.fixture(scope='module')
def module_prn_content_setup(module_target_sat, module_sca_manifest):
    """Fixture to set up content entities to properly test pulp HREF to PRN mapping."""
    return _setup_prn_content(module_target_sat, module_sca_manifest)
