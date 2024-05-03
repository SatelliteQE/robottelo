"""Test module for Dashboard UI

:Requirement: Dashboard

:CaseAutomation: Automated

:CaseComponent: Dashboard

:Team: Endeavour

:CaseImportance: High

"""

from nailgun.entity_mixins import TaskFailedError
import pytest

from robottelo.config import settings
from robottelo.constants import FAKE_7_CUSTOM_PACKAGE
from robottelo.utils.datafactory import gen_string
from robottelo.utils.issue_handlers import is_open


@pytest.mark.tier2
def test_positive_host_configuration_status(session, target_sat):
    """Check if the Host Configuration Status Widget links are working

    :id: ffb0a6a1-2b65-4578-83c7-61492122d865

    :customerscenario: true

    :steps:

        1. Navigate to Monitor -> Dashboard
        2. Review the Host Configuration Status
        3. Navigate to each of the links which has search string associated
           with it.

    :expectedresults: Each link shows the right info

    :BZ: 1631219
    """
    org = target_sat.api.Organization().create()
    loc = target_sat.api.Location().create()
    host = target_sat.api.Host(organization=org, location=loc).create()
    criteria_list = [
        'Hosts that had performed modifications without error',
        'Hosts in error state',
        'Good host reports in the last 30 minutes',
        'Hosts that had pending changes',
        'Out of sync hosts',
        'Hosts with alerts disabled',
        'Hosts with no reports',
    ]
    search_strings_list = [
        'last_report > "30 minutes ago" and (status.applied > 0 or'
        ' status.restarted > 0) and (status.failed = 0)',
        'last_report > "30 minutes ago" and (status.failed > 0 or'
        ' status.failed_restarts > 0) and status.enabled = true',
        'last_report > "30 minutes ago" and status.enabled = true and'
        ' status.applied = 0 and status.failed = 0 and status.pending = 0',
        'last_report > "30 minutes ago" and status.pending > 0 and status.enabled = true',
        'last_report < "30 minutes ago" and status.enabled = true',
        'status.enabled = false',
        'not has last_report and status.enabled = true',
    ]
    if is_open('BZ:1631219'):
        criteria_list.pop()
        search_strings_list.pop()

    with session:
        session.organization.select(org_name=org.name)
        session.location.select(loc_name=loc.name)
        dashboard_values = session.dashboard.read('HostConfigurationStatus')
        for criteria in criteria_list:
            if criteria == 'Hosts with no reports':
                assert dashboard_values['status_list'][criteria] == 1
            else:
                assert dashboard_values['status_list'][criteria] == 0

        for criteria, search in zip(criteria_list, search_strings_list, strict=True):
            if criteria == 'Hosts with no reports':
                session.dashboard.action({'HostConfigurationStatus': {'status_list': criteria}})
                values = session.host.read_all()
                assert values['searchbox'] == search
                assert len(values['table']) == 1
                assert values['table'][0]['Name'] == host.name
            else:
                session.dashboard.action({'HostConfigurationStatus': {'status_list': criteria}})
                values = session.host.read_all()
                assert values['searchbox'] == search
                assert len(values['table']) == 0


@pytest.mark.tier2
def test_positive_host_configuration_chart(session, target_sat):
    """Check if the Host Configuration Chart is working in the Dashboard UI

    :id: b03314aa-4394-44e5-86da-c341c783003d

    :steps:

        1. Navigate to Monitor -> Dashboard
        2. Review the Host Configuration Chart widget
        3. Check that chart contains correct percentage value

    :expectedresults: Chart showing correct data
    """
    org = target_sat.api.Organization().create()
    loc = target_sat.api.Location().create()
    target_sat.api.Host(organization=org, location=loc).create()
    with session:
        session.organization.select(org_name=org.name)
        session.location.select(loc_name=loc.name)
        dashboard_values = session.dashboard.read('HostConfigurationChart')
        assert '100%' in dashboard_values['chart'].values()


@pytest.mark.upgrade
@pytest.mark.run_in_one_thread
@pytest.mark.tier2
def test_positive_task_status(session, target_sat):
    """Check if the Task Status is working in the Dashboard UI and
        filter from Tasks index page is working correctly

    :id: fb667d6a-7255-4341-9f79-2f03d19e8e0f

    :steps:

        1. Navigate to Monitor -> Dashboard
        2. Review the Latest Warning/Error Tasks widget
        3. Review the Running Chart widget
        4. Review the Task Status widget
        5. Review the Stopped Chart widget
        6. Click few links from the widget

    :expectedresults: Each link shows the right info and filter can be set
        from Tasks dashboard

    :BZ: 1718889
    """
    url = 'www.non_existent_repo_url.org'
    org = target_sat.api.Organization().create()
    product = target_sat.api.Product(organization=org).create()
    repo = target_sat.api.Repository(
        url=f'http://{url}', product=product, content_type='yum'
    ).create()
    with pytest.raises(TaskFailedError):
        repo.sync()
    with session:
        session.organization.select(org_name=org.name)
        session.dashboard.action({'TaskStatus': {'state': 'stopped', 'result': 'warning'}})
        searchbox = session.task.read_all('searchbox')
        assert searchbox['searchbox'] == 'state=stopped&result=warning'
        session.task.set_chart_filter('ScheduledChart')
        tasks = session.task.read_all(['ScheduledChart'])
        total_items = session.task.total_items()
        assert total_items == int(tasks['ScheduledChart']['total'].split()[0])
        session.task.set_chart_filter('StoppedChart', {'row': 1, 'focus': 'Total'})
        tasks = session.task.read_all()
        total_items = session.task.total_items()
        assert total_items == int(tasks['StoppedChart']['table'][1]['Total'])
        task_name = f"Synchronize repository '{repo.name}'; product '{product.name}'; organization '{org.name}'"
        assert tasks['table'][0]['Action'] == task_name
        assert tasks['table'][0]['State'] == 'stopped'
        assert tasks['table'][0]['Result'] == 'warning'
        session.dashboard.action({'LatestFailedTasks': {'name': 'Synchronize'}})
        values = session.task.read(task_name)
        assert values['task']['result'] == 'warning'
        assert (
            values['task']['errors']
            == f'Cannot connect to host {url}:80 ssl:default [Name or service not known]'
        )


@pytest.mark.upgrade
@pytest.mark.no_containers
@pytest.mark.run_in_one_thread
@pytest.mark.skip_if_not_set('clients')
@pytest.mark.tier3
@pytest.mark.rhel_ver_match('8')
@pytest.mark.skipif((not settings.robottelo.repos_hosting_url), reason='Missing repos_hosting_url')
@pytest.mark.parametrize(
    'repos_collection',
    [
        {
            'distro': 'rhel8',
            'YumRepository': {'url': settings.repos.yum_3.url},
        }
    ],
    indirect=True,
)
def test_positive_user_access_with_host_filter(
    test_name,
    function_entitlement_manifest_org,
    module_location,
    rhel_contenthost,
    target_sat,
    repos_collection,
):
    """Check if user with necessary host permissions can access dashboard
    and required widgets are rendered with proper values

    :id: 24b4b371-cba0-4bc8-bc6a-294c62e0586d

    :steps:

        1. Specify proper filter with permission for your role
        2. Create new user and assign role to it
        3. Login into application using this new user
        4. Check dashboard and widgets on it
        5. Register new content host to populate some values into dashboard widgets

    :expectedresults: Dashboard and Errata Widget rendered without errors and
        contain proper values

    :BZ: 1417114

    :parametrized: yes
    """
    user_login = gen_string('alpha')
    user_password = gen_string('alphanumeric')
    org = function_entitlement_manifest_org
    lce = target_sat.api.LifecycleEnvironment(organization=org).create()
    # create a role with necessary permissions
    role = target_sat.api.Role().create()
    user_permissions = {
        'Organization': ['view_organizations'],
        'Location': ['view_locations'],
        None: ['access_dashboard'],
        'Host': ['view_hosts'],
    }
    target_sat.api_factory.create_role_permissions(role, user_permissions)
    # create a user and assign the above created role
    target_sat.api.User(
        default_organization=org,
        organization=[org],
        default_location=module_location,
        location=[module_location],
        role=[role],
        login=user_login,
        password=user_password,
    ).create()
    with target_sat.ui_session(test_name, user=user_login, password=user_password) as session:
        assert session.dashboard.read('HostConfigurationStatus')['total_count'] == 0
        assert len(session.dashboard.read('LatestErrata')['erratas']) == 0
        rhel_contenthost.add_rex_key(target_sat)
        repos_collection.setup_content(org.id, lce.id, upload_manifest=False)
        repos_collection.setup_virtual_machine(
            rhel_contenthost, location_title=module_location.name
        )
        rhel_contenthost.run('subscription-manager repos --enable "*"')
        result = rhel_contenthost.run(f'yum install -y {FAKE_7_CUSTOM_PACKAGE}')
        assert result.status == 0
        hostname = rhel_contenthost.hostname
        # Check UI for values
        assert session.host.search(hostname)[0]['Name'] == hostname
        hosts_values = session.dashboard.read('HostConfigurationStatus')
        assert hosts_values['total_count'] == 1
        errata_values = session.dashboard.read('LatestErrata')['erratas']
        assert len(errata_values) == 2
        assert 'security' in [e['Type'] for e in errata_values]
        assert settings.repos.yum_3.errata[25] in [e['Errata'].split()[0] for e in errata_values]


@pytest.mark.tier2
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_sync_overview_widget(session, module_product, module_target_sat):
    """Check if the Sync Overview widget is working in the Dashboard UI

    :id: 553fbe33-0f6f-46fb-8d80-5d1d9ed483cf

    :steps:
        1. Sync some repositories
        2. Navigate to Monitor -> Dashboard
        3. Review the Sync Overview widget

    :expectedresults: Correct data should appear in the widget

    :BZ: 1995424
    """
    repo = module_target_sat.api.Repository(
        url=settings.repos.yum_1.url, product=module_product
    ).create()
    with session:
        session.repository.synchronize(module_product.name, repo.name)
        sync_params = session.dashboard.read('SyncOverview')['syncs']
        assert len(sync_params) == 1
        assert sync_params[0]['Product'] == module_product.name
        assert sync_params[0]['Status'] in ('Syncing Complete.', 'Sync Incomplete')
        assert 'ago' in sync_params[0]['Finished']
