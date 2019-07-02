# -*- encoding: utf-8 -*-
"""Test class for Packages UI

:Requirement: Packages

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: ContentManagement

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from fauxfactory import gen_string
from nailgun import entities

from robottelo import manifests
from robottelo.api.utils import enable_rhrepo_and_fetchid
from robottelo.constants import (
    FAKE_0_YUM_REPO,
    FAKE_3_YUM_REPO,
    RPM_TO_UPLOAD,
)

from robottelo.decorators import fixture, tier2, upgrade
from robottelo.helpers import get_data_file

from robottelo.products import SatelliteToolsRepository


@fixture(scope='module')
def module_org():
    return entities.Organization().create()


@fixture(scope='module')
def module_product(module_org):
    return entities.Product(organization=module_org).create()


@fixture(scope='module')
def module_yum_repo(module_product):
    yum_repo = entities.Repository(
        name=gen_string('alpha'),
        product=module_product,
        content_type='yum',
        url=FAKE_0_YUM_REPO,
    ).create()
    yum_repo.sync()
    return yum_repo


@fixture(scope='module')
def module_yum_repo2(module_product):
    yum_repo = entities.Repository(
        name=gen_string('alpha'),
        product=module_product,
        content_type='yum',
        url=FAKE_3_YUM_REPO,
    ).create()
    yum_repo.sync()
    return yum_repo


@fixture(scope='module')
def module_rh_repo(module_org):
    manifests.upload_manifest_locked(module_org.id, manifests.clone())
    rhst = SatelliteToolsRepository(cdn=True)
    repo_id = enable_rhrepo_and_fetchid(
        basearch=rhst.data['arch'],
        org_id=module_org.id,
        product=rhst.data['product'],
        repo=rhst.data['repository'],
        reposet=rhst.data['repository-set'],
        releasever=rhst.data['releasever'],
    )
    entities.Repository(id=repo_id).sync()
    return entities.Repository(id=repo_id).read()


@tier2
def test_positive_search_in_repo(session, module_org, module_yum_repo):
    """Create product with yum repository assigned to it. Search for
    packages inside of it

    :id: e182a89f-74e4-4b29-8152-1ea3bd014fd3

    :expectedresults: Content search functionality works as intended and
        expected packages are present inside of repository

    :CaseLevel: Integration
    """
    with session:
        session.organization.select(org_name=module_org.name)
        assert session.package.search(
            'name = bear', repository=module_yum_repo.name
        )[0]['RPM'].startswith('bear')
        assert session.package.search(
            'name = cheetah', repository=module_yum_repo.name
        )[0]['RPM'].startswith('cheetah')


@tier2
@upgrade
def test_positive_search_in_multiple_repos(
        session, module_org, module_yum_repo, module_yum_repo2):
    """Create product with two different yum repositories assigned to it.
    Search for packages inside of these repositories. Make sure that unique
    packages present in corresponding repos.

    :id: 249ac04b-8e31-42e9-ac37-08608bf867a1

    :expectedresults: Content search functionality works as intended and
        expected packages are present inside of repositories

    :BZ: 1514457

    :CaseLevel: Integration
    """
    with session:
        session.organization.select(org_name=module_org.name)
        assert session.package.search(
            'name = tiger')[0]['RPM'].startswith('tiger')
        assert session.package.search(
            'name = Lizard')[0]['RPM'].startswith('Lizard')
        # First repository
        assert session.package.search(
            'name = tiger', repository=module_yum_repo.name
        )[0]['RPM'].startswith('tiger')
        assert not session.package.search(
            'name = Lizard', repository=module_yum_repo.name
        )
        # Second repository
        assert session.package.search(
            'name = Lizard', repository=module_yum_repo2.name
        )[0]['RPM'].startswith('Lizard')
        assert not session.package.search(
            'name = tiger', repository=module_yum_repo2.name
        )


@tier2
@upgrade
def test_positive_check_package_details(session, module_org, module_yum_repo):
    """Create product with yum repository assigned to it. Search for
    package inside of it and then open it. Check all the details about that
    package

    :id: 57625386-4a9e-4bea-b2d5-d97326043150

    :expectedresults: Package is present inside of repository and has all
        expected values in details section

    :CaseLevel: Integration
    """
    with session:
        session.organization.select(org_name=module_org.name)
        expected_package_details = {
            'description': 'A dummy package of gorilla',
            'summary': 'A dummy package of gorilla',
            'group': 'Internet/Applications',
            'license': 'GPLv2',
            'url': 'http://tstrachota.fedorapeople.org',
            'size': '2.39 KB (2452 Bytes)',
            'filename': 'gorilla-0.62-1.noarch.rpm',
            'checksum': ('ffd511be32adbf91fa0b3f54f23cd1c02add50578344'
                         'ff8de44cea4f4ab5aa37'),
            'checksum_type': 'sha256',
            'source_rpm': 'gorilla-0.62-1.src.rpm',
            'build_host': 'smqe-ws15',
            'build_time': '1331831364',
        }
        all_package_details = session.package.read(
            'gorilla', repository=module_yum_repo.name)['details']
        package_details = {
            key: value for key, value in all_package_details.items()
            if key in expected_package_details
        }
        assert expected_package_details == package_details


@tier2
@upgrade
def test_positive_check_custom_package_details(
        session, module_org, module_yum_repo):
    """Upload custom rpm package to repository. Search for package
    and then open it. Check that package details are available

    :id: 679622a7-003e-4887-8622-b95b9468da7d

    :expectedresults: Package is present inside of repository and it
        possible to view its details

    :CaseLevel: Integration

    :BZ: 1387766, 1394390
    """
    with open(get_data_file(RPM_TO_UPLOAD), 'rb') as handle:
        module_yum_repo.upload_content(files={'content': handle})
    with session:
        session.organization.select(org_name=module_org.name)
        assert session.package.search(
            'filename = {0}'.format(RPM_TO_UPLOAD),
            repository=module_yum_repo.name
        )[0]['RPM'] == RPM_TO_UPLOAD.replace('.rpm', '')
        repo_details = session.package.read(
            RPM_TO_UPLOAD.split('-')[0],
            repository=module_yum_repo.name
        )['details']
        assert repo_details['filename'] == RPM_TO_UPLOAD


@tier2
@upgrade
def test_positive_rh_repo_search_and_check_file_list(
        session, module_org, module_rh_repo):
    """Synchronize one of RH repos (for example Satellite Tools). Search
    for packages inside of it and open one of the packages and check list of
    files inside of it.

    :id: 9fae92be-6d63-40d8-983b-a6eb54bbed3e

    :expectedresults: Content search functionality works as intended and
        package contains expected list of files

    :CaseLevel: System
    """
    with session:
        session.organization.select(org_name=module_org.name)
        assert session.package.search(
            'name = {0}'.format('facter'),
            repository=module_rh_repo.name,
        )[0]['RPM'].startswith('facter')
        assert session.package.search(
            'name = {0}'.format('katello-host-tools'),
            repository=module_rh_repo.name
        )[0]['RPM'].startswith('katello-host-tools')
        package_details = session.package.read(
            'katello-agent', repository=module_rh_repo.name)
        assert {
            '/usr/lib/gofer/plugins/katelloplugin.py',
            '/usr/lib/yum-plugins',
            '/usr/lib/yum-plugins/package_upload.py',
            '/usr/sbin/katello-package-upload',
        }.issubset(set(package_details['files']['package_files']))
