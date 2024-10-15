"""Test class for Packages UI

:Requirement: Repositories

:CaseAutomation: Automated

:CaseComponent: Repositories

:team: Phoenix-content

:CaseImportance: High

"""

from fauxfactory import gen_string
import pytest

from robottelo.config import settings
from robottelo.constants import DEFAULT_LOC, PRDS, REPOS, REPOSET, RPM_TO_UPLOAD, DataFile


@pytest.fixture(scope='module')
def module_org(module_target_sat):
    return module_target_sat.api.Organization().create()


@pytest.fixture(scope='module')
def module_product(module_org, module_target_sat):
    return module_target_sat.api.Product(organization=module_org).create()


@pytest.fixture(scope='module')
def module_yum_repo(module_product, module_target_sat):
    yum_repo = module_target_sat.api.Repository(
        name=gen_string('alpha'),
        product=module_product,
        content_type='yum',
        url=settings.repos.yum_0.url,
    ).create()
    yum_repo.sync()
    return yum_repo


@pytest.fixture(scope='module')
def module_yum_repo2(module_product, module_target_sat):
    yum_repo = module_target_sat.api.Repository(
        name=gen_string('alpha'),
        product=module_product,
        content_type='yum',
        url=settings.repos.yum_3.url,
    ).create()
    yum_repo.sync()
    return yum_repo


@pytest.fixture(scope='module')
def module_rh_repo(module_sca_manifest_org, module_target_sat):
    rhsc = module_target_sat.cli_factory.SatelliteCapsuleRepository(cdn=True)
    repo_id = module_target_sat.api_factory.enable_rhrepo_and_fetchid(
        basearch=rhsc.data['arch'],
        org_id=module_sca_manifest_org.id,
        product=rhsc.data['product'],
        repo=rhsc.data['repository'],
        reposet=rhsc.data['repository-set'],
        releasever=rhsc.data['releasever'],
    )
    module_target_sat.api.Repository(id=repo_id).sync()
    return module_target_sat.api.Repository(id=repo_id).read()


@pytest.fixture(scope='module')
def module_rhel8_repo(module_sca_manifest_org, module_target_sat):
    "Enable and sync rhel8 appstream repository"
    return module_target_sat.cli_factory.setup_org_for_a_rh_repo(
        {
            'product': PRDS['rhel8'],
            'repository-set': REPOSET['rhel8_aps'],
            'repository': REPOS['rhel8_aps']['name'],
            'organization-id': module_sca_manifest_org.id,
            'releasever': REPOS['rhel8_aps']['releasever'],
        },
        force_use_cdn=True,
    )


@pytest.mark.rhel_ver_match('8')
@pytest.mark.no_containers
def test_positive_parse_package_name_url(
    session, module_target_sat, module_sca_manifest_org, module_rhel8_repo, rhel_contenthost
):
    """
    Check the links present on Package details page are correctly parse plus signs on Hosts page

    :id: d73c75ff-f422-439b-b97f-5901e7268a7c

    :steps:
        1. Go to content > content types > packages
        2. Search for a package from a module (eg httpd-2.4.37-65.module+el8.10.0+22069+b47f5c72.1.x86_64)
        3. click on the package link
        4. click on any links "Installed On", "Applicable To" or "Upgradable For"

    :expectedresults: Satellite search for applicable_rpms=followed by package name, including the plus signs,
        Search box on Hosts page should not omitted the plus signs

    :customerscenario: true

    :Verifies: SAT-26967
    """

    activation_key = module_target_sat.cli.ActivationKey.info(
        {'id': module_rhel8_repo['activationkey-id']}
    )
    rhel_contenthost.register(
        activation_keys=activation_key['name'],
        target=module_target_sat,
        org=module_sca_manifest_org,
        loc=None,
    )
    assert rhel_contenthost.subscribed

    with module_target_sat.ui_session() as session:
        session.organization.select(org_name=module_sca_manifest_org.name)
        session.location.select(DEFAULT_LOC)
        pkg_httpd = session.package.search('name = httpd')[0]
        assert '+' in pkg_httpd['RPM']
        session.package.click_install_on_link('httpd')

        session.browser.switch_to_window(session.browser.window_handles[1])

        read_searchbox_value = session.host.read_filled_searchbox()
        assert '+' in read_searchbox_value
        assert 'installed_package=' + pkg_httpd['RPM'] == read_searchbox_value

        session.browser.close_window()


@pytest.mark.tier2
def test_positive_search_in_repo(session, module_org, module_yum_repo):
    """Create product with yum repository assigned to it. Search for
    packages inside of it

    :id: e182a89f-74e4-4b29-8152-1ea3bd014fd3

    :expectedresults: Content search functionality works as intended and
        expected packages are present inside of repository
    """
    with session:
        session.organization.select(org_name=module_org.name)
        assert session.package.search('name = bear', repository=module_yum_repo.name)[0][
            'RPM'
        ].startswith('bear')
        assert session.package.search('name = cheetah', repository=module_yum_repo.name)[0][
            'RPM'
        ].startswith('cheetah')


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_search_in_multiple_repos(session, module_org, module_yum_repo, module_yum_repo2):
    """Create product with two different yum repositories assigned to it.
    Search for packages inside of these repositories. Make sure that unique
    packages present in corresponding repos.

    :id: 249ac04b-8e31-42e9-ac37-08608bf867a1

    :expectedresults: Content search functionality works as intended and
        expected packages are present inside of repositories

    :BZ: 1514457
    """
    with session:
        session.organization.select(org_name=module_org.name)
        assert session.package.search('name = tiger')[0]['RPM'].startswith('tiger')
        assert session.package.search('name = ant')[0]['RPM'].startswith('ant')
        # First repository
        assert session.package.search('name = tiger', repository=module_yum_repo.name)[0][
            'RPM'
        ].startswith('tiger')
        assert not session.package.search('name = ant', repository=module_yum_repo.name)
        # Second repository
        assert session.package.search('name = ant', repository=module_yum_repo2.name)[0][
            'RPM'
        ].startswith('ant')
        assert not session.package.search('name = tiger', repository=module_yum_repo2.name)


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_check_package_details(session, module_org, module_yum_repo):
    """Create product with yum repository assigned to it. Search for
    package inside of it and then open it. Check all the details about that
    package

    :id: 57625386-4a9e-4bea-b2d5-d97326043150

    :expectedresults: Package is present inside of repository and has all
        expected values in details section

    :customerscenario: true
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
            'checksum': ('ffd511be32adbf91fa0b3f54f23cd1c02add50578344ff8de44cea4f4ab5aa37'),
            'checksum_type': 'sha256',
            'source_rpm': 'gorilla-0.62-1.src.rpm',
            'build_host': 'smqe-ws15',
            'build_time': 'March 15, 2012, 05:09 PM',
        }
        all_package_details = session.package.read('gorilla', repository=module_yum_repo.name)[
            'details'
        ]
        package_details = {
            key: value
            for key, value in all_package_details.items()
            if key in expected_package_details
        }
        assert expected_package_details == package_details


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_check_custom_package_details(session, module_org, module_yum_repo):
    """Upload custom rpm package to repository. Search for package
    and then open it. Check that package details are available

    :id: 679622a7-003e-4887-8622-b95b9468da7d

    :expectedresults: Package is present inside of repository and it
        possible to view its details

    :customerscenario: true

    :BZ: 1387766, 1394390
    """
    module_yum_repo.upload_content(files={'content': DataFile.RPM_TO_UPLOAD.read_bytes()})
    with session:
        session.organization.select(org_name=module_org.name)
        assert session.package.search(
            f'filename = {RPM_TO_UPLOAD}', repository=module_yum_repo.name
        )[0]['RPM'] == RPM_TO_UPLOAD.replace('.rpm', '')
        repo_details = session.package.read(
            RPM_TO_UPLOAD.split('-')[0], repository=module_yum_repo.name
        )['details']
        assert repo_details['filename'] == RPM_TO_UPLOAD


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_rh_repo_search_and_check_file_list(session, module_org, module_rh_repo):
    """Synchronize one of RH repos (for example Satellite Capsule). Search
    for packages inside of it and open one of the packages and check list of
    files inside of it.

    :id: 9fae92be-6d63-40d8-983b-a6eb54bbed3e

    :expectedresults: Content search functionality works as intended and
        package contains expected list of files
    """
    with session:
        session.organization.select(org_name=module_org.name)
        assert session.package.search(
            'name = {}'.format('foreman-proxy'), repository=module_rh_repo.name
        )[0]['RPM'].startswith('foreman-proxy')
        assert session.package.search(
            'name = {}'.format('satellite-capsule'), repository=module_rh_repo.name
        )[0]['RPM'].startswith('satellite-capsule')
        package_details = session.package.read(
            'satellite-installer', repository=module_rh_repo.name
        )
        assert {
            '/etc/foreman-installer/scenarios.d/capsule-answers.yaml',
            '/etc/foreman-installer/scenarios.d/capsule.migrations',
            '/etc/foreman-installer/scenarios.d/capsule.yaml',
            '/etc/foreman-installer/scenarios.d/satellite-answers.yaml',
            '/etc/foreman-installer/scenarios.d/satellite.migrations',
            '/usr/share/satellite-installer/bin',
            '/usr/share/satellite-installer/bin/capsule-installer',
            '/usr/share/satellite-installer/bin/katello-installer',
        }.issubset(set(package_details['files']['package_files']))
