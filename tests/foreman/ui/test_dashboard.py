"""Test module for Dashboard UI

:Requirement: Dashboard

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Dashboard

:Assignee: ogajduse

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from airgun.session import Session
from nailgun import entities
from nailgun.entity_mixins import TaskFailedError

from robottelo.api.utils import create_role_permissions
from robottelo.config import settings
from robottelo.constants import FAKE_1_CUSTOM_PACKAGE
from robottelo.datafactory import gen_string
from robottelo.utils.issue_handlers import is_open


@pytest.mark.tier2
def test_positive_host_configuration_status(session):
    """Check if the Host Configuration Status Widget links are working

    :id: ffb0a6a1-2b65-4578-83c7-61492122d865

    :customerscenario: true

    :Steps:

        1. Navigate to Monitor -> Dashboard
        2. Review the Host Configuration Status
        3. Navigate to each of the links which has search string associated
           with it.

    :expectedresults: Each link shows the right info

    :BZ: 1631219

    :CaseLevel: Integration
    """
    org = entities.Organization().create()
    loc = entities.Location().create()
    host = entities.Host(organization=org, location=loc).create()
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
        'last_report > \"30 minutes ago\" and (status.applied > 0 or'
        ' status.restarted > 0) and (status.failed = 0)',
        'last_report > \"30 minutes ago\" and (status.failed > 0 or'
        ' status.failed_restarts > 0) and status.enabled = true',
        'last_report > \"30 minutes ago\" and status.enabled = true and'
        ' status.applied = 0 and status.failed = 0 and status.pending = 0',
        'last_report > \"30 minutes ago\" and status.pending > 0 and status.enabled = true',
        'last_report < \"30 minutes ago\" and status.enabled = true',
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

        for criteria, search in zip(criteria_list, search_strings_list):
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
def test_positive_host_configuration_chart(session):
    """Check if the Host Configuration Chart is working in the Dashboard UI

    :id: b03314aa-4394-44e5-86da-c341c783003d

    :Steps:

        1. Navigate to Monitor -> Dashboard
        2. Review the Host Configuration Chart widget
        3. Check that chart contains correct percentage value

    :expectedresults: Chart showing correct data

    :CaseLevel: Integration
    """
    org = entities.Organization().create()
    loc = entities.Location().create()
    entities.Host(organization=org, location=loc).create()
    with session:
        session.organization.select(org_name=org.name)
        session.location.select(loc_name=loc.name)
        dashboard_values = session.dashboard.read('HostConfigurationChart')
        assert '100%' in dashboard_values['chart'].values()


@pytest.mark.upgrade
@pytest.mark.run_in_one_thread
@pytest.mark.tier2
def test_positive_task_status(session):
    """Check if the Task Status is working in the Dashboard UI and
        filter from Tasks index page is working correctly

    :id: fb667d6a-7255-4341-9f79-2f03d19e8e0f

    :Steps:

        1. Navigate to Monitor -> Dashboard
        2. Review the Latest Warning/Error Tasks widget
        3. Review the Running Chart widget
        4. Review the Task Status widget
        5. Review the Stopped Chart widget
        6. Click few links from the widget

    :expectedresults: Each link shows the right info and filter can be set
        from Tasks dashboard

    :BZ: 1718889

    :CaseLevel: Integration
    """
    url = 'www.non_existent_repo_url.org'
    org = entities.Organization().create()
    product = entities.Product(organization=org).create()
    repo = entities.Repository(url=f'http://{url}', product=product, content_type='yum').create()
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
        task_name = "Synchronize repository '{}'; product '{}'; organization '{}'".format(
            repo.name, product.name, org.name
        )
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
@pytest.mark.run_in_one_thread
@pytest.mark.skip_if_not_set('clients')
@pytest.mark.tier3
@pytest.mark.skipif((not settings.robottelo.repos_hosting_url), reason='Missing repos_hosting_url')
@pytest.mark.parametrize(
    'repos_collection',
    [
        {
            'distro': 'rhel7',
            'SatelliteToolsRepository': {},
            'YumRepository': {'url': settings.repos.yum_6.url},
        },
    ],
    indirect=True,
)
def test_positive_user_access_with_host_filter(
    test_name, module_location, rhel7_contenthost, target_sat, repos_collection
):
    """Check if user with necessary host permissions can access dashboard
    and required widgets are rendered with proper values

    :id: 24b4b371-cba0-4bc8-bc6a-294c62e0586d

    :Steps:

        1. Specify proper filter with permission for your role
        2. Create new user and assign role to it
        3. Login into application using this new user
        4. Check dashboard and widgets on it
        5. Register new content host to populate some values into dashboard widgets

    :expectedresults: Dashboard and Errata Widget rendered without errors and
        contain proper values

    :BZ: 1417114

    :parametrized: yes

    :CaseLevel: System
    """
    user_login = gen_string('alpha')
    user_password = gen_string('alphanumeric')
    org = entities.Organization().create()
    lce = entities.LifecycleEnvironment(organization=org).create()
    # create a role with necessary permissions
    role = entities.Role().create()
    user_permissions = {
        'Organization': ['view_organizations'],
        'Location': ['view_locations'],
        None: ['access_dashboard'],
        'Host': ['view_hosts'],
    }
    create_role_permissions(role, user_permissions)
    # create a user and assign the above created role
    entities.User(
        default_organization=org,
        organization=[org],
        default_location=module_location,
        location=[module_location],
        role=[role],
        login=user_login,
        password=user_password,
    ).create()
    with Session(test_name, user=user_login, password=user_password) as session:
        assert session.dashboard.read('HostConfigurationStatus')['total_count'] == 0
        assert len(session.dashboard.read('LatestErrata')['erratas']) == 0
        repos_collection.setup_content(org.id, lce.id, upload_manifest=True)
        repos_collection.setup_virtual_machine(
            rhel7_contenthost, location_title=module_location.name
        )
        result = rhel7_contenthost.run(f'yum install -y {FAKE_1_CUSTOM_PACKAGE}')
        assert result.status == 0
        hostname = rhel7_contenthost.hostname
        # Check UI for values
        assert session.host.search(hostname)[0]['Name'] == hostname
        hosts_values = session.dashboard.read('HostConfigurationStatus')
        assert hosts_values['total_count'] == 1
        errata_values = session.dashboard.read('LatestErrata')['erratas']
        assert len(errata_values) == 1
        assert errata_values[0]['Type'] == 'security'
        assert settings.repos.yum_6.errata[2] in errata_values[0]['Errata']


@pytest.mark.tier2
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_sync_overview_widget(session, module_org, module_product):

    """Check if the Sync Overview widget is working in the Dashboard UI

    :id: 553fbe33-0f6f-46fb-8d80-5d1d9ed483cf

    :Steps:
        1. Sync some repositories
        2. Navigate to Monitor -> Dashboard
        3. Review the Sync Overview widget

    :expectedresults: Correct data should appear in the widget

    :BZ: 1995424

    :CaseLevel: Integration
    """
    repo = entities.Repository(url=settings.repos.yum_1.url, product=module_product).create()
    with session:
        session.repository.synchronize(module_product.name, repo.name)
        sync_params = session.dashboard.read('SyncOverview')['syncs']
        assert len(sync_params) == 1
        assert sync_params[0]['Product'] == module_product.name
        assert sync_params[0]['Status'] in ('Syncing Complete.', 'Sync Incomplete')
        assert 'ago' in sync_params[0]['Finished']
