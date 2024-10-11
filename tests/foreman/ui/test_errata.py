"""UI Tests for the errata management feature

:Requirement: Errata

:CaseAutomation: Automated

:CaseComponent: ErrataManagement

:team: Phoenix-content

:CaseImportance: High

"""

from datetime import datetime, timedelta
import re

from broker import Broker
from dateutil.parser import parse
from fauxfactory import gen_string
import pytest
from selenium.common.exceptions import NoSuchElementException
from wait_for import wait_for

from robottelo import constants
from robottelo.config import settings
from robottelo.constants import (
    DEFAULT_LOC,
    FAKE_1_CUSTOM_PACKAGE,
    FAKE_1_CUSTOM_PACKAGE_NAME,
    FAKE_2_CUSTOM_PACKAGE,
    FAKE_3_YUM_OUTDATED_PACKAGES,
    FAKE_4_CUSTOM_PACKAGE,
    FAKE_5_CUSTOM_PACKAGE,
    FAKE_9_YUM_OUTDATED_PACKAGES,
    FAKE_9_YUM_SECURITY_ERRATUM,
    FAKE_9_YUM_SECURITY_ERRATUM_COUNT,
    FAKE_10_YUM_BUGFIX_ERRATUM,
    FAKE_10_YUM_BUGFIX_ERRATUM_COUNT,
    FAKE_11_YUM_ENHANCEMENT_ERRATUM,
    FAKE_11_YUM_ENHANCEMENT_ERRATUM_COUNT,
    PRDS,
    REAL_0_RH_PACKAGE,
    REAL_4_ERRATA_CVES,
    REAL_4_ERRATA_ID,
    REAL_RHEL8_1_ERRATA_ID,
    REAL_RHEL8_ERRATA_CVES,
    REAL_RHSCLIENT_ERRATA,
)
from robottelo.hosts import ContentHost
from robottelo.utils.issue_handlers import is_open

CUSTOM_REPO_URL = settings.repos.yum_9.url
CUSTOM_REPO_ERRATA = settings.repos.yum_9.errata
CUSTOM_REPO_ERRATA_ID = settings.repos.yum_9.errata[0]

CUSTOM_REPO_3_URL = settings.repos.yum_3.url
CUSTOM_REPO_3_ERRATA = settings.repos.yum_3.errata
CUSTOM_REPO_3_ERRATA_ID = settings.repos.yum_3.errata[0]

RHVA_PACKAGE = REAL_0_RH_PACKAGE
RHVA_ERRATA_ID = REAL_4_ERRATA_ID
RHVA_ERRATA_CVES = REAL_4_ERRATA_CVES

pytestmark = [pytest.mark.run_in_one_thread]


def _generate_errata_applicability(hostname, module_target_sat):
    """Force host to generate errata applicability"""
    host = module_target_sat.api.Host().search(query={'search': f'name={hostname}'})[0].read()
    host.errata_applicability(synchronous=False)


def _set_setting_value(setting_entity, value):
    """Set setting value.

    :param setting_entity: the setting entity instance.
    :param value: The setting value to set.
    """
    setting_entity.value = value
    setting_entity.update(['value'])


@pytest.fixture
def errata_status_installable(module_target_sat):
    """Fixture to allow restoring errata_status_installable setting after usage"""
    errata_status_installable = module_target_sat.api.Setting().search(
        query={'search': 'name="errata_status_installable"'}
    )[0]
    original_value = errata_status_installable.value
    yield errata_status_installable
    _set_setting_value(errata_status_installable, original_value)


def cv_publish_promote(sat, org, cv, lce=None, needs_publish=True):
    """Publish & promote Content View Version with all content visible in org.

    :param lce: if None, default to 'Library',
        pass a single instance of lce, or list of instances.
        do not pass the Library environment.
    :param bool needs_publish: if False, skip publish of a new version
    :return dictionary:
        'content-view': instance of updated cv
        'content-view-version': instance of newest cv version
    """
    # Default to 'Library' lce, if None passed
    # Take a single instance of lce, or list of instances
    lce_ids = 'Library'
    if lce is not None:
        lce_ids = [lce.id] if not isinstance(lce, list) else sorted(_lce.id for _lce in lce)

    if needs_publish is True:
        _publish_and_wait(sat, org, cv)
    # Content-view must have at least one published version
    cv = sat.api.ContentView(id=cv.id).read()
    assert cv.version, f'No version(s) are published to the Content-View: {cv.id}'
    # Find highest version id, will be the latest
    cvv_id = max(cvv.id for cvv in cv.version)
    # Promote to lifecycle-environment(s)
    if lce_ids == 'Library':
        library_lce = cv.environment[0].read()
        sat.api.ContentViewVersion(id=cvv_id).promote(
            data={'environment_ids': library_lce.id, 'force': 'True'}
        )
    else:
        sat.api.ContentViewVersion(id=cvv_id).promote(data={'environment_ids': lce_ids})
    _result = {
        'content-view': sat.api.ContentView(id=cv.id).read(),
        'content-view-version': sat.api.ContentViewVersion(id=cvv_id).read(),
    }
    assert all(
        entry for entry in _result.values()
    ), f'One or more necessary components are missing: {_result}'
    return _result


def _publish_and_wait(sat, org, cv, timeout=60):
    """Synchrnous publish of a new version of content-view to organization,
    wait for task completion.

    return: the polled task, success or fail.
    """
    task_id = sat.api.ContentView(id=cv.id).publish({'id': cv.id, 'organization': org})['id']
    assert task_id, f'No task was invoked to publish the Content-View: {cv.id}.'
    # Should take < 1 minute, check in 5s intervals
    sat.wait_for_tasks(
        search_query=(f'label = Actions::Katello::ContentView::Publish and id = {task_id}'),
        search_rate=5,
        max_tries=round(timeout / 5),
    )
    return sat.api.ForemanTask(id=task_id).poll(must_succeed=False)


@pytest.fixture
def registered_contenthost(
    module_sca_manifest_org,
    module_target_sat,
    rhel_contenthost,
    module_product,
    module_lce,
    module_ak,
    module_cv,
    request,
    repos=None,
):
    """RHEL ContentHost registered in satellite,
    Using SCA and global registration.

    :note: rhel_contenthost will be parametrized by rhel6 to 9, also -fips for all distros.
        to use specific rhel version parametrized contenthost;
        use `pytest.mark.rhel_ver_match('[]')` to mark contenthost rhel major version(s)
            for tests using this fixture.

    :environment: Defaults to module_lce.
        To use Library environment for activation key / content-view:
        pass the string 'Library' (not case sensative) in the list of params.

    :repos: pass as a parametrized request
        list of upstream URLs for custom repositories.
            default: None; repo enablement will be sklipped for host.
                if None, add any repos to cv/ak, publish/promote etc, after calling fixture.
        example:
            @pytest.mark.parametrize('registered_contenthost',
                [[repo1_url, repo2_url,]],
                indirect=True,
            )
        for Library env:
            @pytest.mark.parametrize('registered_contenthost',
                [['library', repo1_url, repo2_url,]],
                indirect=True,
            )
        for Default: no repos, use module_cv, module_ak, module_lce:
            no need to parametrize fixture, just import it.
            if desired, still parametrize registered host's rhel major version(s):
                eg. pytest.mark.rhel_ver_match('[8, 9, ...]') etc.

    """
    params = getattr(request, 'param', None)
    environment = module_lce
    if params is None:
        repos = []
    else:
        if any(p.lower() == 'library' for p in params):
            environment = 'Library'
        repos = [p for p in params if str(p).lower() != 'library']

    if rhel_contenthost.subscribed:
        rhel_contenthost.unregister()
    custom_repos = []
    for repo_url in repos:
        new_repo = module_target_sat.api.Repository(url=repo_url, product=module_product).create()
        new_repo.sync()
        custom_repos.append(new_repo)
    if len(custom_repos) > 0:
        module_cv.repository = custom_repos
        module_cv.update(['repository'])
    # Publish/promote CV if needed, associate entities, register client:
    # skip enabling repos, we will do after, with subscription-manager
    setup = module_target_sat.api_factory.register_host_and_needed_setup(
        organization=module_sca_manifest_org,
        client=rhel_contenthost,
        activation_key=module_ak,
        environment=environment,
        content_view=module_cv,
    )

    @request.addfinalizer
    # Cleanup for in-between parametrized sessions,
    # unregister the host if it's still subscribed to content.
    def cleanup():
        nonlocal setup
        client = setup['client']
        if client is not None:
            if client.subscribed:
                client.unregister()
            assert not client.subscribed, (
                f'Failed to unregister the host client: {client.hostname}, was unable to fully teardown host.'
                ' Client retains some content association.'
            )

    # no error setting up fixtures and registering client
    assert setup['result'] != 'error', f'{setup["message"]}'
    assert (client := setup['client'])
    # nothing applicable to start
    result = client.execute('subscription-manager repos')
    assert client.applicable_errata_count == 0
    assert client.applicable_package_count == 0
    # if no repos given, subscription-manager should report error
    if len(repos) == 0:
        assert client.execute(r'subscription-manager repos --enable \*').status == 1
    # any custom repos in host are setup, and can be synced again,
    # we can also enable each repo with subscription-manager:
    else:
        # list all repos available to sub-manager:
        sub_manager_repos = client.execute('subscription-manager repos --list')
        repo_ids_names = {'ids': [], 'names': []}
        for line in sub_manager_repos.stdout.splitlines():
            # in each output line, check for Name: and ID: of repos listed
            if search := re.search(r'ID: (.*)', line):
                id_found = search.group(1).strip()
                repo_ids_names['ids'].append(id_found)
            if search := re.search(r'Name: (.*)', line):
                name_found = search.group(1).strip()
                repo_ids_names['names'].append(name_found)
        # every repo id found, has a corresponding name we will match to satellite repo
        assert len(repo_ids_names['ids']) == len(repo_ids_names['names']), (
            f"Failed to extract a given repository's name, and or id, from subscription-manager list."
            f" {sub_manager_repos}"
        )

        for repo in custom_repos:
            # sync repository to satellite
            assert module_target_sat.api.Repository(id=repo.id).read()
            result = repo.sync()['humanized']
            assert (
                len(result['errors']) == 0
            ), f'Failed to sync custom repository [id: {repo.id}]:\n{str(result["errors"])}'
            # found index (repo) with matching name, grab sub-manager repo-id:
            assert repo.name in repo_ids_names['names']
            sub_man_repo_id = repo_ids_names['ids'][repo_ids_names['names'].index(repo.name)]
            # repo can be enabled by id without error
            enable_repo = client.execute(f'subscription-manager repos --enable {sub_man_repo_id}')
            assert enable_repo.status == 0, (
                f'Failed to enable a repository with subscription-manager, on client: {client.hostname}.'
                f' {enable_repo.stderr}'
            )
        assert len(custom_repos) == len(repo_ids_names['ids'])
        assert all(name in repo_ids_names['names'] for r in custom_repos for name in [r.name])

    return client


@pytest.mark.e2e
@pytest.mark.tier3
@pytest.mark.rhel_ver_match('[^6]')
@pytest.mark.parametrize('registered_contenthost', [[CUSTOM_REPO_URL]], indirect=True)
@pytest.mark.no_containers
def test_end_to_end(
    registered_contenthost,
    module_target_sat,
    module_product,
    module_lce,
    module_cv,
    session,
):
    """Create all entities required for errata, register an applicable host,
    read errata details and apply it to host.

    :id: a26182fc-f31a-493f-b094-3f5f8d2ece47

    :setup: A host with content from a custom repo,
        contains some outdated packages applicable errata.

    :expectedresults: Errata details are the same as expected, errata
        installation is successful.

    :parametrized: yes

    :verifies: SAT-23414, SAT-7998

    :customerscenario: true
    """

    ERRATA_DETAILS = {
        'advisory': 'RHSA-2012:0055',
        'cves': 'N/A',
        'type': 'Security Advisory',
        'severity': 'N/A',
        'reboot_suggested': 'No',
        'topic': '',
        'description': 'Sea_Erratum',
        'issued': '2012-01-27',
        'last_updated_on': '2012-01-27',
        'solution': '',
    }
    ERRATA_PACKAGES = {
        'independent_packages': [
            'penguin-0.9.1-1.noarch',
            'shark-0.1-1.noarch',
            'walrus-5.21-1.noarch',
        ],
        'module_stream_packages': [],
    }
    # client was registered with single custom repo
    client = registered_contenthost
    hostname = client.hostname
    assert client.subscribed
    custom_repo = module_cv.read().repository[0].read()
    # nothing applicable to start
    assert (
        0 == client.applicable_errata_count == client.applicable_package_count
    ), f'Expected no applicable erratum or packages to start, on host: {hostname}'

    # install outdated package version, making an errata applicable
    result = client.execute(f'yum install -y {FAKE_1_CUSTOM_PACKAGE}')
    assert (
        result.status == 0
    ), f'Failed to install package {FAKE_1_CUSTOM_PACKAGE}.\n{result.stdout}'
    # recalculate and assert app errata, after installing outdated pkg
    assert client.execute('subscription-manager repos').status == 0
    applicable_errata = client.applicable_errata_count
    assert (
        applicable_errata == 1
    ), f'Expected 1 applicable errata: {CUSTOM_REPO_ERRATA_ID}, after setup. Got {applicable_errata}'

    with session:
        datetime_utc_start = datetime.utcnow().replace(microsecond=0)
        # Check selection box function for BZ#1688636
        session.location.select(loc_name=DEFAULT_LOC)
        results = session.errata.search_content_hosts(
            entity_name=CUSTOM_REPO_ERRATA_ID,
            value=hostname,
            environment=module_lce.name,
        )
        assert len(results) == 1
        # BZ 2265095: Check default columns in table of applicable host:
        # from ContentTypes > Errata > Details > Content Hosts tab
        assert results[0]['Name'] == hostname
        if not is_open('SAT-23414'):
            assert str(client.deploy_rhel_version) in results[0]['OS']
            assert results[0]['Environment'] == module_lce.name
            assert results[0]['Content View'] == module_cv.name
        # Check errata details
        errata = session.errata.read(CUSTOM_REPO_ERRATA_ID)
        assert errata['repositories']['table'], (
            f'There are no repositories listed for errata ({CUSTOM_REPO_ERRATA_ID}),',
            f' expected to find at least one repository, name: {custom_repo.name}.',
        )
        # repo/product entry in table match expected
        # find the first table entry with the custom repository's name
        errata_repo = next(
            (
                repo
                for repo in errata['repositories']['table']
                if 'Name' in repo and repo['Name'] == custom_repo.name
            ),
            None,
        )
        # assert custom repo found and product name
        assert (
            errata_repo
        ), f'Could not find the errata repository in UI by name: {custom_repo.name}.'
        assert errata_repo['Name'] == custom_repo.name
        assert (
            errata_repo['Product'] == module_product.name
        ), 'The product name for the errata repository in UI does not match.'
        # Check all tabs of Errata Details page
        assert (
            not ERRATA_DETAILS.items() - errata['details'].items()
        ), 'Errata details do not match expected values.'
        assert parse(errata['details']['issued']) == parse(
            ERRATA_DETAILS['issued']
        ), 'Errata issued date in UI does not match.'
        assert parse(errata['details']['last_updated_on']) == parse(
            ERRATA_DETAILS['last_updated_on']
        ), 'Errata last updated date in UI does not match.'
        assert set(errata['packages']['independent_packages']) == set(
            ERRATA_PACKAGES['independent_packages']
        ), 'Set of errata packages in UI does not match.'
        assert (
            errata['packages']['module_stream_packages']
            == ERRATA_PACKAGES['module_stream_packages']
        ), 'Errata module streams in UI does not match.'
        # Apply Errata, find REX install task
        session.host_new.apply_erratas(
            entity_name=hostname,
            search=f"errata_id == {CUSTOM_REPO_ERRATA_ID}",
        )
        install_query = (
            f'"Install errata errata_id == {CUSTOM_REPO_ERRATA_ID} on {hostname}"'
            f' and started_at >= {datetime_utc_start - timedelta(seconds=1)}'
        )
        results = module_target_sat.wait_for_tasks(
            search_query=install_query,
            search_rate=2,
            max_tries=60,
        )
        # should only be one task from this host after timestamp
        assert (
            len(results) == 1
        ), f'Expected just one errata install task, but found {len(results)}.\nsearch_query: {install_query}'
        task_status = module_target_sat.api.ForemanTask(id=results[0].id).poll()
        assert (
            task_status['result'] == 'success'
        ), f'Errata Installation task failed:\n{task_status}'
        assert (
            client.applicable_errata_count == 0
        ), f'Unexpected applicable errata found after install of {CUSTOM_REPO_ERRATA_ID}.'
        # UTC timing for install task and session
        _UTC_format = '%Y-%m-%d %H:%M:%S UTC'
        install_start = datetime.strptime(task_status['started_at'], _UTC_format)
        install_end = datetime.strptime(task_status['ended_at'], _UTC_format)
        # install task duration did not exceed 1 minute,
        #   duration since start of session did not exceed 10 minutes.
        assert (install_end - install_start).total_seconds() <= 60
        assert (install_end - datetime_utc_start).total_seconds() <= 600
        # Find bulk generate applicability task
        results = module_target_sat.wait_for_tasks(
            search_query=(f'Bulk generate applicability for host {hostname}'),
            search_rate=2,
            max_tries=60,
        )
        results.sort(key=lambda res: res.id)
        task_status = module_target_sat.api.ForemanTask(id=results[-1].id).poll()
        assert (
            task_status['result'] == 'success'
        ), f'Bulk Generate Errata Applicability task failed:\n{task_status}'
        # UTC timing for generate applicability task
        bulk_gen_start = datetime.strptime(task_status['started_at'], _UTC_format)
        bulk_gen_end = datetime.strptime(task_status['ended_at'], _UTC_format)
        assert (bulk_gen_start - install_end).total_seconds() <= 30
        assert (bulk_gen_end - bulk_gen_start).total_seconds() <= 60

        # Errata should still be visible on satellite, but not on contenthost
        assert session.errata.read(CUSTOM_REPO_ERRATA_ID)
        results = session.errata.search_content_hosts(
            entity_name=CUSTOM_REPO_ERRATA_ID,
            value=hostname,
            environment=module_lce.name,
        )
        assert len(results) == 0
        # Check package version was updated on contenthost
        _package_version = client.execute(f'rpm -q {FAKE_1_CUSTOM_PACKAGE_NAME}').stdout
        assert FAKE_2_CUSTOM_PACKAGE in _package_version


@pytest.mark.tier2
@pytest.mark.no_containers
@pytest.mark.rhel_ver_match('8')
@pytest.mark.parametrize('registered_contenthost', [[CUSTOM_REPO_3_URL]], indirect=True)
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_host_content_errata_tab_pagination(
    module_sca_manifest_org,
    registered_contenthost,
    module_target_sat,
    module_lce,
    module_cv,
    session,
):
    """
    # Test per-page pagination for BZ#1662254
    # Test apply by REX using Select All for BZ#1846670

    :setup:
        1. rhel8 registered contenthost with custom repos enabled.
        2. enable and sync rh repository.
        3. add rh repo to cv for registered host and publish/promote.

    :id: 6363eda7-a162-4a4a-b70f-75decbd8202e

    :steps:
        1. Install more than 20 packages that need errata
        2. View Content Host's Errata page
        3. Assert total_pages > 1
        4. Change per-page setting to 50
        5. Assert table has more than 20 errata
        6. Change per-page setting to 5
        7. Assert setting changed and more total-pages now
        8. Search and select one available errata and install it.
        9. Assert total items in table is one less.
        10. Assert per page count and total pages has not changed.
        11. Use the selection box on the left to select all on this page and others.
            All errata, from all pages, are selected. Select all YYY.
        12. Click the drop down arrow to the right of "Apply All", click Submit.
        13. Assert All Errata were applied, none are available anymore.
        14. Assert no pagination on new host UI>content>errata.
        15. Raise `NoSuchElementException` when looking for a pagination element.

    :expectedresults: More than just the current page of errata can be selected
        and applied, with changed per-page settings.

    :customerscenario: true

    :BZ: 1662254, 1846670
    """
    org = module_sca_manifest_org
    # custom_repo was created & added to cv, enabled in registered_contenthost.
    repos = [
        repo.read() for repo in module_cv.read().repository if repo.read().url == CUSTOM_REPO_3_URL
    ]
    assert len(repos) > 0
    custom_repo = repos[0]
    custom_repo.sync()
    # Set up and sync rh_repo
    rh_repo_id = module_target_sat.api_factory.enable_sync_redhat_repo(
        constants.REPOS['rhst8'],
        module_sca_manifest_org.id,
    )
    # add rh_repo to cv, publish version and promote w/ the repository
    module_target_sat.cli.ContentView.add_repository(
        {
            'id': module_cv.id,
            'organization-id': org.id,
            'repository-id': rh_repo_id,
        }
    )
    module_cv = module_cv.read()
    cv_publish_promote(
        module_target_sat,
        org,
        module_cv,
        module_lce,
    )
    registered_contenthost.add_rex_key(satellite=module_target_sat)
    assert registered_contenthost.execute(r'subscription-manager repos --enable \*').status == 0
    _chost_name = registered_contenthost.hostname
    # Install all YUM 3 packages
    pkgs = ' '.join(FAKE_3_YUM_OUTDATED_PACKAGES)
    assert registered_contenthost.execute(f'yum install -y {pkgs}').status == 0

    with session:
        session.location.select(loc_name=DEFAULT_LOC)
        # Go to new host's page UI, Content>Errata tab,
        # There are two pagination objects on errata tab, we read the top one
        pf4_pagination = session.host_new.get_errata_pagination(_chost_name)
        assert pf4_pagination.read()
        assert pf4_pagination.current_per_page == 20
        # assert total_pages > 1 with default page settings
        assert pf4_pagination.total_pages > 1
        assert pf4_pagination.current_page == 1
        assert pf4_pagination.total_items == registered_contenthost.applicable_errata_count
        # Change per-page setting to 50, and assert there is now only one page
        pf4_pagination.set_per_page(50)
        pf4_pagination = session.host_new.get_errata_pagination(_chost_name)
        assert pf4_pagination.read()
        assert pf4_pagination.current_per_page == 50
        assert pf4_pagination.current_page == 1
        assert pf4_pagination.total_pages == 1
        # assert at least the 28 errata from fake repo are present
        assert pf4_pagination.total_items >= 28
        _prior_app_count = pf4_pagination.total_items
        # Change to a low per-page setting of 5
        pf4_pagination.set_per_page(5)
        pf4_pagination = session.host_new.get_errata_pagination(_chost_name)
        assert pf4_pagination.read()
        assert pf4_pagination.current_per_page == 5
        assert pf4_pagination.current_page == 1
        assert pf4_pagination.total_pages > 2
        _prior_pagination = pf4_pagination.read()

        # Install one available errata from UI with REX by default
        errata_id = CUSTOM_REPO_3_ERRATA[1]
        session.host_new.apply_erratas(_chost_name, f'errata_id="{errata_id}"')
        # find host errata install job and status, timeout is 120s
        # may take some time, wait for any not pending
        status = module_target_sat.wait_for_tasks(
            search_query=(f'Remote action: Install errata on {_chost_name} and result != pending'),
            search_rate=2,
            max_tries=60,
        )
        assert len(status) >= 1
        task = status[0]
        assert task.result == 'success'
        assert 'host' in task.input
        assert registered_contenthost.nailgun_host.id == task.input['host']['id']
        # find bulk applicability task and status
        status = module_target_sat.wait_for_tasks(
            search_query=(
                f'Bulk generate applicability for host {_chost_name} and result != pending'
            ),
            search_rate=2,
            max_tries=60,
        )
        assert len(status) >= 1
        task = status[0]
        assert task.result == 'success'
        assert 'host_ids' in task.input
        assert registered_contenthost.nailgun_host.id in task.input['host_ids']
        # applicable errata is now one less
        assert registered_contenthost.applicable_errata_count == _prior_app_count - 1
        # wait for the tab to load with updated pagination, sat may be slow, timeout 30s.
        # lambda: read is not the same as prior pagination read, and is also not empty {}.
        _invalid_pagination = ({}, _prior_pagination)
        session.browser.refresh()
        wait_for(
            lambda: session.host_new.get_errata_pagination(_chost_name).read()
            not in _invalid_pagination,
            timeout=30,
            delay=5,
        )
        # read updated pagination, handle slower UI loading
        pf4_pagination = session.host_new.get_errata_pagination(_chost_name)
        assert (_read_page := pf4_pagination.read())
        assert _read_page != _prior_pagination
        assert pf4_pagination.current_page == 1
        # total_items decreased by one
        item_count = pf4_pagination.total_items
        assert item_count == _prior_app_count - 1

        # Install All available from errata tab, we pass no search filter,
        # so that all errata are selected, on all pages.
        session.host_new.apply_erratas(_chost_name)
        # find host's errata install job non-pending, timeout is 120s
        status = module_target_sat.wait_for_tasks(
            search_query=(f'Remote action: Install errata on {_chost_name} and result != pending'),
            search_rate=2,
            max_tries=60,
        )
        assert len(status) >= 1
        task = status[0]
        assert task.result == 'success'
        assert 'host' in task.input
        assert registered_contenthost.nailgun_host.id == task.input['host']['id']
        # find bulk applicability task and status
        status = module_target_sat.wait_for_tasks(
            search_query=(
                f'Bulk generate applicability for host {_chost_name} and result != pending'
            ),
            search_rate=2,
            max_tries=60,
        )
        assert len(status) >= 1
        task = status[0]
        assert task.result == 'success'
        assert 'host_ids' in task.input
        assert registered_contenthost.nailgun_host.id in task.input['host_ids']
        # check there are no applicable errata left for Chost
        assert registered_contenthost.applicable_errata_count == 0
        # The errata table is not present when empty, it should not be paginated.
        _items = -1
        _ex_raised = False
        session.browser.refresh()
        try:
            wait_for(
                lambda: not session.host_new.get_errata_pagination(_chost_name).read(),
                timeout=30,
                delay=5,
            )
        except NoSuchElementException:
            # pagination read raised exception, does not exist
            _ex_raised = True
        if not _ex_raised:
            # pagination exists, reads empty {}, but we expect an
            # exception when looking for a pagination element:
            pf4_pagination = session.host_new.get_errata_pagination(_chost_name)
            # exception trying to find element
            with pytest.raises(NoSuchElementException):
                _items = pf4_pagination.total_items
            # assert nothing was found to update value
            assert (
                _items == -1
            ), f'Found updated pagination total_items: {_items}, but expected to be empty.'
            # would get failure at pytest.raises if no matching exception
            _ex_raised = True
        assert (
            _ex_raised
        ), 'Search for empty pagination did not raise expected `NoSuchElementException`.'


@pytest.mark.tier2
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_list(target_sat, session):
    """View all errata in an Org

    :id: 71c7a054-a644-4c1e-b304-6bc34ea143f4

    :setup:
        1. two separate organizations, one custom product existing in each org.

    :steps:
        1. Create and sync separate repositories for each org.
        2. Go to UI > Content Types > Errata page.

    :expectedresults: Check that the errata belonging to one Org is not showing in the other.

    :BZ: 1659941, 1837767

    :customerscenario: true
    """
    # new orgs, because module and function ones will overlap with other tests
    org_0 = target_sat.api.Organization().create()
    product_0 = target_sat.api.Product(organization=org_0).create()
    org_1 = target_sat.api.Organization().create()
    product_1 = target_sat.api.Product(organization=org_1).create()
    # create and sync repository, for first org's errata
    repo_0 = target_sat.api.Repository(
        url=CUSTOM_REPO_URL,
        product=product_0,
    ).create()
    repo_0.sync()
    # create and sync repo, for other org's errata
    repo_1 = target_sat.api.Repository(
        url=CUSTOM_REPO_3_URL,
        product=product_1,
    ).create()
    repo_1.sync()

    with session:
        # View in first organization
        session.organization.select(org_name=org_0.name)
        assert (
            session.errata.search(CUSTOM_REPO_ERRATA_ID, applicable=False)[0]['Errata ID']
            == CUSTOM_REPO_ERRATA_ID
        ), f'Could not find expected errata: {CUSTOM_REPO_ERRATA_ID}, in org: {org_0.name}.'

        assert not session.errata.search(CUSTOM_REPO_3_ERRATA_ID, applicable=False), (
            f'Found orgs ({org_1.name}) errata: {CUSTOM_REPO_3_ERRATA_ID},'
            f' in other org ({org_0.name}) as well.'
        )
        # View in other organization
        session.organization.select(org_name=org_1.name)
        assert (
            session.errata.search(CUSTOM_REPO_3_ERRATA_ID, applicable=False)[0]['Errata ID']
            == CUSTOM_REPO_3_ERRATA_ID
        ), f'Could not find expected errata: {CUSTOM_REPO_3_ERRATA_ID}, in org: {org_1.name}.'

        assert not session.errata.search(CUSTOM_REPO_ERRATA_ID, applicable=False), (
            f'Found orgs ({org_0.name}) errata: {CUSTOM_REPO_ERRATA_ID},'
            f' in other org ({org_1.name}) as well.'
        )


@pytest.mark.tier2
def test_positive_list_permission(
    test_name,
    module_target_sat,
    function_product,
    function_sca_manifest_org,
):
    """Show errata only if the User has permissions to view them

    :id: cdb28f6a-23df-47a2-88ab-cd3b492126b2

    :Setup:

        1. Create two products with one repo each. Sync them.
        2. Make sure that they both have errata.
        3. Create a user with view access on one product and not on the other.

    :steps: Go to Content -> Errata.

    :expectedresults: Check that the new user is able to see errata for one
        product only.
    """
    module_target_sat.api_factory.enable_sync_redhat_repo(
        constants.REPOS['rhsclient8'],
        function_sca_manifest_org.id,
    )
    custom_repo = module_target_sat.api.Repository(
        url=CUSTOM_REPO_URL, product=function_product
    ).create()
    custom_repo.sync()
    # create role with access only to 'RHEL8' RedHat product
    role = module_target_sat.api.Role().create()
    module_target_sat.api.Filter(
        organization=[function_sca_manifest_org],
        permission=module_target_sat.api.Permission().search(
            query={'search': 'resource_type="Katello::Product"'}
        ),
        role=role,
        search=f'name = "{PRDS["rhel8"]}"',
    ).create()
    # generate login credentials for new role
    user_password = gen_string('alphanumeric')
    user = module_target_sat.api.User(
        default_organization=function_sca_manifest_org,
        organization=[function_sca_manifest_org],
        role=[role],
        password=user_password,
    ).create()

    with module_target_sat.ui_session(
        test_name, user=user.login, password=user_password
    ) as session:
        # can view RHSC8 product's repo content (RHSC8 errata_id)
        assert (
            session.errata.search(REAL_RHSCLIENT_ERRATA, applicable=False)[0]['Errata ID']
            == REAL_RHSCLIENT_ERRATA
        )
        # cannot view function product's custom repo content (fake custom errata_id)
        assert not session.errata.search(CUSTOM_REPO_ERRATA_ID, applicable=False)


@pytest.mark.e2e
@pytest.mark.tier2
@pytest.mark.upgrade
@pytest.mark.no_containers
def test_positive_apply_for_all_hosts(
    module_sca_manifest_org,
    module_product,
    target_sat,
    module_lce,
    module_cv,
    module_ak,
    session,
):
    """Apply an erratum for all content hosts

    :id: d70a1bee-67f4-4883-a0b9-2ccc08a91738

    :Setup: Errata synced on satellite server.

    :customerscenario: true

    :setup:
        1. Create and sync one custom repo for all hosts, add to a content-view.
        2. Checkout four rhel9 contenthosts via Broker.
        3. Register all of the hosts to the same AK, CV, single repo.

    :steps:
        1. Go to Content -> Errata. Select an erratum -> Content Hosts tab.
        2. Select all Content Hosts and apply the erratum.

    :expectedresults: Check that the erratum is applied in all the content
        hosts.
    """
    num_hosts = 4
    distro = 'rhel9'
    # one custom repo on satellite, for all hosts to use
    custom_repo = target_sat.api.Repository(url=CUSTOM_REPO_URL, product=module_product).create()
    custom_repo.sync()
    module_cv.repository = [custom_repo]
    module_cv.update(['repository'])
    with Broker(
        nick=distro,
        workflow='deploy-rhel',
        host_class=ContentHost,
        _count=num_hosts,
        deploy_network_type='ipv6' if settings.server.is_ipv6 else 'ipv4',
    ) as hosts:
        if not isinstance(hosts, list) or len(hosts) != num_hosts:
            pytest.fail('Failed to provision the expected number of hosts.')
        for client in hosts:
            # setup/register all hosts to same ak, content-view, and the one custom repo
            setup = target_sat.api_factory.register_host_and_needed_setup(
                organization=module_sca_manifest_org,
                client=client,
                activation_key=module_ak,
                environment=module_lce,
                content_view=module_cv,
                enable_repos=True,
            )
            assert setup['result'] != 'error', f'{setup["message"]}'
            assert (client := setup['client'])
            assert client.subscribed
            # install all outdated packages
            pkgs = ' '.join(FAKE_9_YUM_OUTDATED_PACKAGES)
            assert client.execute(f'yum install -y {pkgs}').status == 0
            # update and check applicability
            assert client.execute('subscription-manager repos').status == 0
            assert client.applicable_errata_count > 0
            assert client.applicable_package_count > 0

        with session:
            timestamp = datetime.utcnow().replace(microsecond=0) - timedelta(seconds=1)
            session.location.select(loc_name=DEFAULT_LOC)
            # for first errata, apply to all chosts at once,
            # from ContentTypes > Errata > info > ContentHosts tab
            errata_id = settings.repos.yum_9.errata[4]  # RHBA-2012:1030
            result = session.errata.install(
                entity_name=errata_id,
                host_names='All',
            )
            assert result['overview']['job_status'] == 'Success'
            # find single hosts job
            hosts_job = target_sat.wait_for_tasks(
                search_query=(
                    f'Run hosts job: Install errata {errata_id}' f' and started_at >= {timestamp}'
                ),
                search_rate=2,
                max_tries=60,
            )
            assert len(hosts_job) == 1
            # find multiple install tasks, one for each host
            install_tasks = target_sat.wait_for_tasks(
                search_query=(
                    f'Remote action: Install errata {errata_id} on'
                    f' and started_at >= {timestamp}'
                ),
                search_rate=2,
                max_tries=60,
            )
            assert len(install_tasks) == num_hosts
            # find single bulk applicability task for hosts
            applicability_task = target_sat.wait_for_tasks(
                search_query=(
                    'Bulk generate applicability for hosts' f' and started_at >= {timestamp}'
                ),
                search_rate=2,
                max_tries=60,
            )
            assert len(applicability_task) == 1
            # found updated kangaroo package in each host
            updated_version = '0.2-1.noarch'
            for client in hosts:
                updated_pkg = session.host_new.get_packages(
                    entity_name=client.hostname, search='kangaroo'
                )
                assert len(updated_pkg['table']) == 1
                assert updated_pkg['table'][0]['Installed version'] == updated_version

            # for second errata, install in each chost and check, one at a time.
            # from Legacy Chost UI > details > Errata tab
            for client in hosts:
                status = session.contenthost.install_errata(
                    client.hostname, CUSTOM_REPO_ERRATA_ID, install_via='rex'
                )
                assert status['overview']['job_status'] == 'Success'
                assert status['overview']['job_status_progress'] == '100%'
                # check updated package in chost details
                assert client.execute('subscription-manager repos').status == 0
                packages_rows = session.contenthost.search_package(
                    client.hostname, FAKE_2_CUSTOM_PACKAGE
                )
                # updated walrus package found for each host
                assert packages_rows[0]['Installed Package'] == FAKE_2_CUSTOM_PACKAGE


@pytest.mark.tier2
@pytest.mark.upgrade
@pytest.mark.rhel_ver_match('8')
def test_positive_view_cve(session, module_product, module_sca_manifest_org, target_sat):
    """View CVE number(s) in Errata Details page

    :id: e1c2de13-fed8-448e-b618-c2adb6e82a35

    :Setup: Errata synced on satellite server.

    :steps: Go to Content -> Errata.  Select an Errata.

    :expectedresults:

        1. Check if the CVE information is shown in Errata Details page.
        2. Check if 'N/A' is displayed if CVE information is not present.
    """
    target_sat.api_factory.enable_sync_redhat_repo(
        constants.REPOS['rhst8'],
        module_sca_manifest_org.id,
    )
    custom_repo = target_sat.api.Repository(url=CUSTOM_REPO_URL, product=module_product).create()
    custom_repo.sync()

    with session:
        session.location.select(loc_name=DEFAULT_LOC)
        errata_values = session.errata.read(REAL_RHEL8_1_ERRATA_ID)
        assert errata_values['details']['cves']
        assert {cve.strip() for cve in errata_values['details']['cves'].split(',')} == set(
            REAL_RHEL8_ERRATA_CVES
        )
        errata_values = session.errata.read(CUSTOM_REPO_ERRATA_ID)
        assert errata_values['details']['cves'] == 'N/A'


@pytest.mark.tier3
@pytest.mark.upgrade
def test_positive_filter_by_environment(
    module_sca_manifest_org,
    module_product,
    target_sat,
    module_lce,
    module_cv,
    module_ak,
    session,
):
    """Filter Content hosts by environment

    :id: 578c3a92-c4d8-4933-b122-7ff511c276ec

    :customerscenario: true

    :BZ: 1383729

    :Setup: Errata synced on satellite server.

    :steps: Go to Content -> Errata.  Select an Errata -> Content Hosts tab
        -> Filter content hosts by Environment.

    :expectedresults: Content hosts can be filtered by Environment.
    """
    org = module_sca_manifest_org
    # one custom repo on satellite, for all hosts to use
    custom_repo = target_sat.api.Repository(url=CUSTOM_REPO_URL, product=module_product).create()
    custom_repo.sync()
    module_cv.repository = [custom_repo]
    module_cv.update(['repository'])

    with Broker(nick='rhel8', host_class=ContentHost, _count=3) as clients:
        for client in clients:
            # register all hosts to the same AK, CV:
            setup = target_sat.api_factory.register_host_and_needed_setup(
                organization=module_sca_manifest_org,
                client=client,
                activation_key=module_ak,
                environment=module_lce,
                content_view=module_cv,
                enable_repos=True,
            )
            assert setup['result'] != 'error', f'{setup["message"]}'
            assert (client := setup['client'])
            assert client.subscribed
            assert client.execute(f'yum install -y {FAKE_1_CUSTOM_PACKAGE}').status == 0

        # Promote the latest content view version to a new lifecycle environment
        content_view = setup['content_view'].read()
        content_view.version.sort(key=lambda version: version.id)
        content_view_version = content_view.version[-1].read()
        lce = content_view_version.environment[-1].read()
        new_lce = target_sat.api.LifecycleEnvironment(organization=org, prior=lce).create()
        content_view_version.promote(data={'environment_ids': new_lce.id})
        host = (
            target_sat.api.Host().search(query={'search': f'name={clients[0].hostname}'})[0].read()
        )
        host.content_facet_attributes = {
            'content_view_id': content_view.id,
            'lifecycle_environment_id': new_lce.id,
        }
        host.update(['content_facet_attributes'])

        with session:
            session.location.select(loc_name=DEFAULT_LOC)
            # search in new_lce
            values = session.errata.search_content_hosts(
                CUSTOM_REPO_ERRATA_ID, clients[0].hostname, environment=new_lce.name
            )
            assert values[0]['Name'] == clients[0].hostname
            assert not session.errata.search_content_hosts(
                CUSTOM_REPO_ERRATA_ID, clients[1].hostname, environment=new_lce.name
            )
            # search in module_lce
            values = session.errata.search_content_hosts(
                CUSTOM_REPO_ERRATA_ID, clients[1].hostname, environment=lce.name
            )
            assert values[0]['Name'] == clients[1].hostname
            assert not session.errata.search_content_hosts(
                CUSTOM_REPO_ERRATA_ID, clients[0].hostname, environment=lce.name
            )


@pytest.mark.tier3
@pytest.mark.upgrade
@pytest.mark.parametrize(
    'registered_contenthost',
    [[CUSTOM_REPO_URL]],
    indirect=True,
)
@pytest.mark.rhel_ver_match('8')
def test_positive_content_host_previous_env(
    session,
    module_cv,
    module_lce,
    module_target_sat,
    registered_contenthost,
    module_sca_manifest_org,
):
    """Check if the applicable errata are available from the content
    host's previous environment

    :id: 78110ba8-3942-46dd-8c14-bffa1dbd5195

    :Setup:
        1. Make sure multiple environments are present, one registered host.
            note: registered_contenthost is using module_lce, module_cv.
        2. Content host's previous environments have additional errata.
        3. Promote the Host's content view version to a new lifecycle environment.
        4. Set the Host to use the new environment, and original content view.

    :Steps: Go to Content Hosts -> Select content host -> Errata Tab ->
        Select Previous environments (Environments Dropdown).

    :expectedresults: The previous environment name, and content view name are correct.
        Expected errata from previous environments are displayed.

    :Verifies: SAT-25213

    :parametrized: yes
    """
    vm = registered_contenthost
    nailgun_host = registered_contenthost.nailgun_host
    assert vm.execute(f'yum install -y {FAKE_1_CUSTOM_PACKAGE}').status == 0
    # Promote the latest content view version to a new lifecycle environment
    new_lce = module_target_sat.api.LifecycleEnvironment(
        organization=module_sca_manifest_org,
        prior=module_lce,
    ).create()
    content_view = module_cv.read()
    content_view.version.sort(key=lambda version: version.id)
    content_view_version = content_view.version[-1].read()
    content_view_version.promote(data={'environment_ids': [new_lce.id]})
    # set host to use {new_lce / module_cv}, prior should be {module_lce / module_cv}
    nailgun_host.content_facet_attributes = {
        'lifecycle_environment_id': new_lce.id,
        'content_view_id': module_cv.id,
    }
    nailgun_host.update(['content_facet_attributes'])
    # new_lce has been set for vm's Current Content Source
    vm_cve = vm.nailgun_host.read().content_facet_attributes['content_view_environments'][0]
    assert vm_cve == nailgun_host.read().content_facet_attributes['content_view_environments'][0]
    assert new_lce.name == vm_cve['lifecycle_environment']['name']
    assert new_lce.id == vm_cve['lifecycle_environment']['id']

    with session:
        session.location.select(loc_name=DEFAULT_LOC)
        # can view errata from previous env, dropdown option is correct
        environment = f'Previous Lifecycle Environment ({module_lce.name}/{content_view.name})'
        content_host_erratum = session.contenthost.search_errata(
            vm.hostname,
            CUSTOM_REPO_ERRATA_ID,
            environment=environment,
        )
        # In Previous Env, expected errata_id was found via search
        assert content_host_erratum[0]['Id'] == CUSTOM_REPO_ERRATA_ID


@pytest.mark.tier2
@pytest.mark.rhel_ver_match('8')
@pytest.mark.parametrize(
    'registered_contenthost',
    [[CUSTOM_REPO_URL]],
    indirect=True,
)
def test_positive_check_errata(session, registered_contenthost):
    """Check if the applicable errata is available from the host page

    :id: 81f3c5bf-5317-40d6-ab3a-2b1a2c5fcbdd

    :steps:
        1. Go to All hosts
        2. Select the host
        3. Content Tab -> Errata Tab
        4. Check the errata

    :expectedresults: The errata is displayed on the host page Content-Errata tab

    :parametrized: yes
    """

    vm = registered_contenthost
    hostname = vm.hostname
    assert vm.execute(f'yum install -y {FAKE_1_CUSTOM_PACKAGE}').status == 0
    with session:
        session.location.select(loc_name=DEFAULT_LOC)
        read_errata = session.host_new.get_details(hostname, 'Content.Errata')
        assert read_errata['Content']['Errata']['table'][0]['Errata'] == CUSTOM_REPO_ERRATA_ID


@pytest.mark.tier3
@pytest.mark.rhel_ver_match('[8, 9]')
@pytest.mark.parametrize(
    'registered_contenthost',
    [['Library', CUSTOM_REPO_URL]],
    indirect=True,
)
def test_positive_host_content_library(
    registered_contenthost,
    function_lce,
    module_lce,
    session,
):
    """Check if the applicable errata are available from the content host's Library.
        View errata table from within All Hosts, and legacy Contenthosts pages.

    :id: a0694930-4bf7-4a97-b275-2be7d5f1b311

    :Setup:
        1. Multiple environments are present, we will use 'Library'.
        2. A registered host's Library environment has some additional errata.

    :steps:
        1. Install the outdated package to registered host, making an errata applicable.
        2. Go to new All Hosts -> Select the host -> Content -> Errata Tab.
        3. Go to Legacy Content Hosts -> Select the host -> Errata Tab -> 'Library' env.
        4. Search for the errata by id. Then, check the entire table without filtering.

    :expectedresults: The expected errata id present in Library is displayed.
        Only a single errata is present, the tables match between the two pages.

    :parametrized: yes
    """
    client = registered_contenthost
    hostname = client.hostname

    assert client.applicable_errata_count == 0
    assert client.execute(f'yum install -y {FAKE_1_CUSTOM_PACKAGE}').status == 0
    assert client.execute('subscription-manager repos').status == 0
    assert client.applicable_errata_count == 1
    assert client.applicable_package_count == 1

    with session:
        session.location.select(loc_name=DEFAULT_LOC)
        # check new host > host > content > errata tab:
        host_tab_search = session.host_new.get_errata_table(
            entity_name=hostname,
            search=f'errata_id="{CUSTOM_REPO_ERRATA_ID}"',
        )
        # found desired errata_id by search
        assert len(host_tab_search) == 1
        assert host_tab_search[0]['Errata'] == CUSTOM_REPO_ERRATA_ID
        # no filters passed, checking all errata present
        host_tab_erratum = session.host_new.get_errata_table(hostname)
        # only the expected errata_id is found
        assert len(host_tab_erratum) == 1
        assert host_tab_erratum[0]['Errata'] == CUSTOM_REPO_ERRATA_ID
        # check legacy chost > chost > errata tab -- search:
        single_chost_search = session.contenthost.search_errata(
            hostname, CUSTOM_REPO_ERRATA_ID, environment='Library Synced Content'
        )
        # found desired errata_id by search
        assert len(single_chost_search) == 1
        assert single_chost_search[0]['Id'] == CUSTOM_REPO_ERRATA_ID
        # display all entries in chost table, only the expected one is present
        all_chost_erratum = session.contenthost.search_errata(
            hostname, errata_id=' ', environment='Library Synced Content'
        )
        assert len(all_chost_erratum) == 1
        assert all_chost_erratum[0]['Id'] == CUSTOM_REPO_ERRATA_ID


@pytest.mark.tier3
@pytest.mark.rhel_ver_match('8')
@pytest.mark.parametrize(
    'registered_contenthost',
    [[CUSTOM_REPO_URL]],
    indirect=True,
)
def test_positive_errata_search_type(session, module_sca_manifest_org, registered_contenthost):
    """Search for errata on a host's page content-errata tab by type.

    :id: f278f0e8-3b64-4dbf-a0c8-b9b289474a76

    :customerscenario: true

    :steps: Search for errata on the host Content-Errata tab by type (e.g. 'type = Security')
        1. Search for "type = Security", assert expected amount and IDs found
        2. Search for "type = Bugfix", assert expected amount and IDs found
        3. Search for "type = Enhancement", assert expected amount and IDs found

    :BZ: 1653293
    """
    vm = registered_contenthost
    pkgs = ' '.join(FAKE_9_YUM_OUTDATED_PACKAGES)
    assert vm.execute(f'yum install -y {pkgs}').status == 0

    with session:
        session.location.select(loc_name=DEFAULT_LOC)
        # Search for RHSA Security errata
        security_erratas = session.host_new.get_errata_by_type(
            entity_name=vm.hostname,
            type='Security',
        )['content']['errata']['table']

        # Assert length matches known amount of RHSA errata
        assert len(security_erratas) == FAKE_9_YUM_SECURITY_ERRATUM_COUNT

        # Assert IDs are that of RHSA errata
        errata_ids = sorted(erratum['Errata'] for erratum in security_erratas)
        assert errata_ids == sorted(FAKE_9_YUM_SECURITY_ERRATUM)
        # Search for RHBA Buxfix errata
        bugfix_erratas = session.host_new.get_errata_by_type(
            entity_name=vm.hostname,
            type='Bugfix',
        )['content']['errata']['table']

        # Assert length matches known amount of RHBA errata
        assert len(bugfix_erratas) == FAKE_10_YUM_BUGFIX_ERRATUM_COUNT

        # Assert IDs are that of RHBA errata
        errata_ids = sorted(erratum['Errata'] for erratum in bugfix_erratas)
        assert errata_ids == sorted(FAKE_10_YUM_BUGFIX_ERRATUM)
        # Search for RHEA Enhancement errata
        enhancement_erratas = session.host_new.get_errata_by_type(
            entity_name=vm.hostname,
            type='Enhancement',
        )['content']['errata']['table']

        # Assert length matches known amount of RHEA errata
        assert len(enhancement_erratas) == FAKE_11_YUM_ENHANCEMENT_ERRATUM_COUNT

        # Assert IDs are that of RHEA errata
        errata_ids = sorted(erratum['Errata'] for erratum in enhancement_erratas)
        assert errata_ids == sorted(FAKE_11_YUM_ENHANCEMENT_ERRATUM)


@pytest.mark.tier3
@pytest.mark.rhel_ver_match('8')
@pytest.mark.parametrize(
    'registered_contenthost',
    [[CUSTOM_REPO_URL]],
    indirect=True,
)
def test_positive_show_count_on_host_pages(session, module_org, registered_contenthost):
    """Available errata by type displayed in New Host>Errata page,
        and expected count by type in Legacy>Content hosts page.

    :id: 8575e282-d56e-41dc-80dd-f5f6224417cb

    :Setup:

        1. Errata synced on satellite server from custom repository.
        2. Registered host, subscribed to promoted CVV, with repo synced to appliable custom packages and erratum.

    :steps:

        1. Go to Hosts -> All Hosts, and Legacy ContentHost -> Hosts.
        2. None of the erratum are installable.
        3. Install all outdated applicable packages via yum.
        4. Recalculate errata applicablity for host.
        5. All of the erratum are now installable, on both pages from step 1.

    :expectedresults:
        The available errata count is displayed and updates.
        Displayed erratum match between the two content host pages.

    :BZ: 1484044, 1775427

    :customerscenario: true
    """
    vm = registered_contenthost
    hostname = vm.hostname
    assert vm.subscribed
    assert vm.execute('subscription-manager repos').status == 0
    assert vm.applicable_errata_count == 0

    with session:
        session.location.select(loc_name=DEFAULT_LOC)
        # new host UI
        new_host_values = session.host_new.search(hostname)
        assert new_host_values[0]['Name'] == hostname
        # None of the erratum are installable
        for errata_type in ('Security', 'Bugfix', 'Enhancement'):
            installable_errata = None
            empty_table = False
            try:
                # exception will be raised in case of unfound element (dropdown or dropdown entry)
                # if an exception was raised, the table is missing/empty (no errata).
                installable_errata = session.host_new.get_errata_by_type(
                    entity_name=hostname,
                    type=errata_type,
                )['content']['errata']['table']
            except Exception:
                empty_table = True
            assert (
                not installable_errata
            ), f'Found some installable {errata_type} errata, when none were expected.'
            assert empty_table
        # legacy contenthost UI
        content_host_values = session.contenthost.search(hostname)
        assert content_host_values[0]['Name'] == hostname
        installable_errata = content_host_values[0]['Installable Updates']['errata']
        for errata_type in ('security', 'bug_fix', 'enhancement'):
            assert (
                int(installable_errata[errata_type]) == 0
            ), f'Found some installable {errata_type} errata, when none were expected.'

        # install outdated packages, recalculate errata applicability
        pkgs = ' '.join(FAKE_9_YUM_OUTDATED_PACKAGES)
        assert vm.execute(f'yum install -y {pkgs}').status == 0
        assert vm.execute('subscription-manager repos').status == 0
        assert vm.applicable_errata_count == 5

        # new host UI (errata tab)
        new_host_values = session.host_new.search(hostname)
        assert new_host_values[0]['Name'] == hostname
        # erratum are installable
        security_errata = session.host_new.get_errata_by_type(
            entity_name=hostname,
            type='Security',
        )['content']['errata']['table']
        assert len(security_errata) == FAKE_9_YUM_SECURITY_ERRATUM_COUNT
        for errata_type in ('Bugfix', 'Enhancement'):
            installable_errata = session.host_new.get_errata_by_type(
                entity_name=hostname,
                type=errata_type,
            )['content']['errata']['table']
            assert (
                len(installable_errata) == 1
            ), f'Expected only one {errata_type} errata to be installable.'
        # legacy contenthost UI
        content_host_values = session.contenthost.search(hostname)
        assert content_host_values[0]['Name'] == hostname
        installable_errata = content_host_values[0]['Installable Updates']['errata']
        # erratum are installable
        assert int(installable_errata['security']) == FAKE_9_YUM_SECURITY_ERRATUM_COUNT
        for errata_type in ('bug_fix', 'enhancement'):
            assert (
                int(installable_errata[errata_type]) == 1
            ), f'Expected only one {errata_type} errata to be installable.'


@pytest.mark.tier3
@pytest.mark.rhel_ver_match('8')
@pytest.mark.parametrize(
    'registered_contenthost',
    [[CUSTOM_REPO_URL]],
    indirect=True,
)
def test_positive_check_errata_counts_by_type_on_host_details_page(
    session,
    module_target_sat,
    module_sca_manifest_org,
    registered_contenthost,
):
    """Errata count on host page

    :id: 89676641-2614-4abb-afed-5c37be396fad

    :Setup:
        1. Errata synced on satellite server.
        2. Some registered host with errata and packages is present.
        3. Install list of outdated packages (FAKE_YUM_9), to the registered host.

    :steps:
        1. Go to All hosts
        2. Select the host
        3. Content Tab -> Errata Tab
        4. Check the counts of the errata types

    :expectedresults:
        1. Packages install succeeds, errata applicability updates automatically.
        2. Correct number of each errata type shown for host.

    """
    vm = registered_contenthost
    hostname = vm.hostname
    with session:
        session.location.select(loc_name=DEFAULT_LOC)
        # from details: no errata to start
        read_errata = session.host_new.get_details(hostname, 'Content.Errata')
        assert int(len(read_errata['Content']['Errata']['pagination'])) == 0

        pkgs = ' '.join(FAKE_9_YUM_OUTDATED_PACKAGES)
        install_timestamp = datetime.utcnow().replace(microsecond=0) - timedelta(seconds=1)
        assert vm.execute(f'yum install -y {pkgs}').status == 0

        # applicability task(s) found and succeed
        applicability_tasks = module_target_sat.wait_for_tasks(
            search_query=(
                f'Bulk generate applicability for host {hostname}'
                f' and started_at >= "{install_timestamp}"'
            ),
            search_rate=2,
            max_tries=60,
        )
        assert len(applicability_tasks) > 0, (
            'No Errata applicability task(s) found after successful yum install.'
            ' Expected at least one task invoked automatically,'
            f' for registered host: {hostname}'
        )
        for task in applicability_tasks:
            assert (result := module_target_sat.api.ForemanTask(id=task.id).poll())
            assert result['result'] == 'success'

        # find newly applicable errata counts by type
        session.browser.refresh()
        errata_type_counts = session.host_new.get_errata_type_counts(entity_name=hostname)
        assert errata_type_counts['Security'] == FAKE_9_YUM_SECURITY_ERRATUM_COUNT
        assert errata_type_counts['Bugfix'] == 1
        assert errata_type_counts['Enhancement'] == 1


@pytest.mark.tier3
@pytest.mark.upgrade
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
@pytest.mark.parametrize('setting_update', ['errata_status_installable'], indirect=True)
@pytest.mark.rhel_ver_match('8')
@pytest.mark.parametrize(
    'registered_contenthost',
    [[CUSTOM_REPO_URL]],
    indirect=True,
)
def test_positive_filtered_errata_status_installable_param(
    errata_status_installable,
    registered_contenthost,
    setting_update,
    module_org,
    target_sat,
    module_lce,
    module_cv,
    session,
):
    """Filter errata for specific content view and verify that host that
    was registered using that content view has different states in
    correspondence to filtered errata and `errata status installable`
    settings flag value

    :id: ed94cf34-b8b9-4411-8edc-5e210ea6af4f

    :setup:
        1. Fixture entities and registered contenthost setup.
        2. Install an outdated package, making an erratum applicable.

    :steps:
        1. Create necessary Content View Filter and Rule for repository errata.
        2. Publish and Promote Content View to a new version containing Filter.
        3. Go to created Host page and check its properties.
        4. Change 'errata status installable' flag in the settings, and
            check host properties once more.

    :expectedresults: Check that 'errata status installable' flag works as intended

    :BZ: 1368254, 2013093

    :CaseImportance: Medium
    """
    client = registered_contenthost
    assert client.execute(f'yum install -y {FAKE_1_CUSTOM_PACKAGE}').status == 0
    assert client.execute('subscription-manager repos').status == 0
    # Adding content view filter and content view filter rule to exclude errata,
    # for the installed package above.
    cv_filter = target_sat.api.ErratumContentViewFilter(
        content_view=module_cv, inclusion=False
    ).create()
    module_cv = module_cv.read()
    module_cv.version.sort(key=lambda version: version.id)
    errata = target_sat.api.Errata(content_view_version=module_cv.version[-1]).search(
        query={'search': f'errata_id="{CUSTOM_REPO_ERRATA_ID}"'}
    )[0]
    target_sat.api.ContentViewFilterRule(content_view_filter=cv_filter, errata=errata).create()
    module_cv = module_cv.read()
    # publish and promote the new version with Filter
    cv_publish_promote(
        target_sat,
        module_org,
        module_cv,
        module_lce,
    )

    with session:
        session.location.select(loc_name=DEFAULT_LOC)
        property_value = 'Yes'
        session.settings.update(f'name = {setting_update.name}', property_value)
        expected_values = {
            'Status': 'OK',
            'Errata': 'All errata applied',
            'Subscription': 'Fully entitled',
        }
        host_details_values = session.host.get_details(client.hostname)
        actual_values = {
            key: value
            for key, value in host_details_values['properties']['properties_table'].items()
            if key in expected_values
        }
        for key in actual_values:
            assert expected_values[key] in actual_values[key], 'Expected text not found'
        property_value = 'Yes'
        session.settings.update(f'name = {setting_update.name}', property_value)
        assert client.execute(f'yum install -y {FAKE_9_YUM_OUTDATED_PACKAGES[1]}').status == 0
        expected_values = {
            'Status': 'Error',
            'Errata': 'Security errata installable',
            'Subscription': 'Fully entitled',
        }
        # Refresh the host page to get newest details
        session.browser.refresh()
        host_details_values = session.host.get_details(client.hostname)
        actual_values = {
            key: value
            for key, value in host_details_values['properties']['properties_table'].items()
            if key in expected_values
        }
        for key in actual_values:
            assert expected_values[key] in actual_values[key], 'Expected text not found'


@pytest.mark.tier3
def test_content_host_errata_search_commands(
    module_product,
    target_sat,
    module_org,
    module_ak,
    module_cv,
    session,
):
    """View a list of affected content hosts for security (RHSA) and bugfix (RHBA) errata,
    filtered with errata status and applicable flags. Applicability is calculated using the
    Library, but Installability is calculated using the attached CV, and is subject to the
    CV's own filtering.

    :id: 45114f8e-0fc8-4c7c-85e0-f9b613530dac

    :Setup:
        1. Two content views, one for each host's repo with errata.
        2. Two registered Content Hosts, one with RHSA and one with RHBA errata.

    :customerscenario: true

    :steps:
        1.  host list --search "errata_status = security_needed"
        2.  host list --search "errata_status = errata_needed"
        3.  host list --search "applicable_errata = RHSA-2012:0055"
        4.  host list --search "applicable_errata = RHBA-2012:1030"
        5.  host list --search "applicable_rpms = walrus-5.21-1.noarch"
        6.  host list --search "applicable_rpms = kangaroo-0.2-1.noarch"
        7.  host list --search installable=True "errata_id = RHSA-2012:0055"
        8.  host list --search installable=True "errata_id = RHBA-2012:1030"

    :expectedresults: The hosts are correctly listed for RHSA and RHBA errata.

    :BZ: 1707335
    """
    content_view = target_sat.api.ContentView(organization=module_org).create()
    RHSA_repo = target_sat.api.Repository(
        url=settings.repos.yum_9.url, product=module_product
    ).create()
    RHBA_repo = target_sat.api.Repository(
        url=settings.repos.yum_6.url, product=module_product
    ).create()
    RHSA_repo.sync()
    RHBA_repo.sync()
    module_cv.repository = [RHSA_repo]
    module_cv.update(['repository'])
    content_view.repository = [RHBA_repo]
    content_view.update(['repository'])
    cvs = [module_cv.read(), content_view.read()]  # client0, client1
    # walrus-0.71-1.noarch (RHSA), kangaroo-0.1-1.noarch (RHBA)
    packages = [FAKE_1_CUSTOM_PACKAGE, FAKE_4_CUSTOM_PACKAGE]
    with Broker(nick='rhel8', host_class=ContentHost, _count=2) as clients:
        for (
            client,
            cv,
            pkg,
        ) in zip(clients, cvs, packages, strict=True):
            setup = target_sat.api_factory.register_host_and_needed_setup(
                organization=module_org,
                client=client,
                activation_key=module_ak,
                environment='Library',
                content_view=cv,
                enable_repos=True,
            )
            assert setup['result'] != 'error', f'{setup["message"]}'
            assert (client := setup['client'])
            assert client.subscribed
            assert client.execute(f'yum install -y {pkg}').status == 0
            assert client.execute('subscription-manager repos').status == 0

        with session:
            session.location.select(loc_name=DEFAULT_LOC)
            # Search for hosts needing RHSA security errata
            result = session.contenthost.search('errata_status = security_needed')
            result = [item['Name'] for item in result]
            assert clients[0].hostname in result, 'Needs-RHSA host not found'
            # Search for hosts needing RHBA bugfix errata
            result = session.contenthost.search('errata_status = errata_needed')
            result = [item['Name'] for item in result]
            assert clients[1].hostname in result, 'Needs-RHBA host not found'
            # Search for applicable RHSA errata by Errata ID
            result = session.contenthost.search(
                f'applicable_errata = {settings.repos.yum_6.errata[2]}'
            )
            result = [item['Name'] for item in result]
            assert clients[0].hostname in result
            # Search for applicable RHBA errata by Errata ID
            result = session.contenthost.search(
                f'applicable_errata = {settings.repos.yum_6.errata[0]}'
            )
            result = [item['Name'] for item in result]
            assert clients[1].hostname in result
            # Search for RHSA applicable RPMs
            result = session.contenthost.search(f'applicable_rpms = {FAKE_2_CUSTOM_PACKAGE}')
            result = [item['Name'] for item in result]
            assert clients[0].hostname in result
            # Search for RHBA applicable RPMs
            result = session.contenthost.search(f'applicable_rpms = {FAKE_5_CUSTOM_PACKAGE}')
            result = [item['Name'] for item in result]
            assert clients[1].hostname in result

            # Search chost for installable RHSA errata by Errata ID
            result = session.contenthost.search_errata(
                entity_name=clients[0].hostname,
                environment='Library Synced Content',
                errata_id=settings.repos.yum_6.errata[2],
            )
            assert len(result) > 0, (
                f'Found no matching entries in chost errata table, for host: {clients[0].hostname}'
                f' searched by errata_id: {settings.repos.yum_6.errata[2]}.'
            )
            for row in result:
                # rows show expected errata details for client
                assert row['Id'] == settings.repos.yum_6.errata[2]
                assert row['Title'] == 'Sea_Erratum'
                assert row['Type'] == 'Security Advisory'

            # Search chost for installable RHBA errata by Errata ID
            result = session.contenthost.search_errata(
                entity_name=clients[1].hostname,
                environment='Library Synced Content',
                errata_id=settings.repos.yum_6.errata[0],
            )
            assert len(result) > 0, (
                f'Found no matching entries in chost errata table, for host: {clients[1].hostname}'
                f' searched by errata_id: {settings.repos.yum_6.errata[0]}.'
            )
            for row in result:
                # rows show expected errata details for client
                assert row['Id'] == settings.repos.yum_6.errata[0]
                assert row['Title'] == 'Kangaroo_Erratum'
                assert row['Type'] == 'Bug Fix Advisory - low'
