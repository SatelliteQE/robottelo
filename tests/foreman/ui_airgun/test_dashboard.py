"""Test module for Dashboard UI

:Requirement: Dashboard

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from airgun.session import Session
from nailgun import entities
from nailgun.entity_mixins import TaskFailedError
from pytest import raises
from requests.exceptions import HTTPError

from robottelo import manifests
from robottelo.api.utils import create_role_permissions, create_sync_custom_repo, promote
from robottelo.constants import (
    DISTRO_RHEL7,
    FAKE_1_CUSTOM_PACKAGE,
    FAKE_2_ERRATA_ID,
    FAKE_6_YUM_REPO,
)
from robottelo.datafactory import gen_string
from robottelo.decorators import (
    bz_bug_is_open,
    run_in_one_thread,
    skip_if_not_set,
    tier2,
    tier3,
    upgrade,
)
from robottelo.products import (
    RepositoryCollection,
    SatelliteToolsRepository,
    YumRepository,
)
from robottelo.vm import VirtualMachine


@tier2
def test_positive_host_configuration_status(session):
    """Check if the Host Configuration Status Widget links are working

    :id: ffb0a6a1-2b65-4578-83c7-61492122d865

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
        'last_report > \"30 minutes ago\" and status.pending > 0'
        ' and status.enabled = true',
        'last_report < \"30 minutes ago\" and status.enabled = true',
        'last_report > \"30 minutes ago\" and status.enabled = false',
        'not has last_report and status.enabled = true',
    ]
    if bz_bug_is_open(1631219):
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
                session.dashboard.action({
                    'HostConfigurationStatus': {'status_list': criteria}
                })
                values = session.host.read_all()
                assert values['searchbox'] == search
                assert len(values['table']) == 1
                assert values['table'][0]['Name'] == host.name
            else:
                session.dashboard.action({
                    'HostConfigurationStatus': {'status_list': criteria}
                })
                values = session.host.read_all()
                assert values['searchbox'] == search
                assert len(values['table']) == 0


@tier2
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
        assert dashboard_values['chart']['No report'] == '100%'


@tier2
def test_positive_new_host(session):
    """Check if the New Hosts widget is working in the Dashboard UI

    :id: 123fadc6-e3e0-4a49-8bca-2bf672460359

    :Steps:

        1. Create new host in the application
        2. Navigate to Monitor -> Dashboard
        3. Review the New Hosts widget

    :expectedresults: New Hosts widget contains information about just created host

    :CaseLevel: Integration
    """
    org = entities.Organization().create()
    loc = entities.Location().create()
    host = entities.Host(organization=org, location=loc).create()
    with session:
        session.organization.select(org_name=org.name)
        session.location.select(loc_name=loc.name)
        dashboard_values = session.dashboard.read('NewHosts')['hosts']
        assert len(dashboard_values) == 1
        assert dashboard_values[0]['Host'] == host.name
        assert host.operatingsystem.read().name in dashboard_values[0]['Operating System']
        assert dashboard_values[0]['Installed'] == '-'


@run_in_one_thread
@tier2
def test_positive_task_status(session):
    """Check if the Task Status is working in the Dashboard UI

    :id: fb667d6a-7255-4341-9f79-2f03d19e8e0f

    :Steps:

        1. Navigate to Monitor -> Dashboard
        2. Review the Task Status widget
        3. Click few links from the widget

    :expectedresults: Each link shows the right info

    :CaseLevel: Integration
    """
    url = 'http://www.non_existent_repo_url.org/repos'
    org = entities.Organization().create()
    product = entities.Product(organization=org).create()
    repo = entities.Repository(
        url=url, product=product, content_type='puppet').create()
    with raises(TaskFailedError):
        repo.sync()
    with session:
        session.organization.select(org_name=org.name)
        session.dashboard.action({
            'TaskStatus': {'state': 'running', 'result': 'pending'}
        })
        tasks = session.task.read_all()
        assert tasks['searchbox'] == 'state=running&result=pending'
        session.dashboard.action({
            'TaskStatus': {'state': 'stopped', 'result': 'warning'}
        })
        tasks = session.task.read_all()
        assert tasks['searchbox'] == 'state=stopped&result=warning'
        assert (
            tasks['table'][0]['Action'] ==
            "Synchronize repository '{}'; product '{}'; "
            "organization '{}'".format(repo.name, product.name, org.name))
        assert tasks['table'][0]['State'] == 'stopped'
        assert tasks['table'][0]['Result'] == 'warning'


@tier2
def test_positive_latest_warning_error_tasks(session):
    """Check if the Latest Warning/Error Tasks Status widget is working in the
    Dashboard UI

    :id: c90df864-1472-4b7c-91e6-9ea9e98384a9

    :Steps:

        1. Navigate to Monitor -> Dashboard
        2. Review the Latest Warning/Error Tasks widget.

    :expectedresults: Link to just failed task is working properly

    :CaseLevel: Integration
    """
    name = entities.Organization().create().name
    with raises(HTTPError):
        entities.Organization(name=name).create()
    with session:
        session.organization.select(org_name=name)
        session.dashboard.action({
            'LatestFailedTasks': {'name': 'Create'}
        })
        values = session.task.read('Create')
        assert values['task']['result'] == 'error'
        assert (
            values['task']['errors'] ==
            'Validation failed: Name has already been taken'
        )


@tier2
def test_positive_content_view_history(session):
    """Check if the Content View History are working in the Dashboard UI

    :id: cb63a67d-7cca-4d2c-9abf-9f4f5e92c856

    :Steps:

        1. Navigate to Monitor -> Dashboard
        2. Review the Content View History widget

    :expectedresults: Each Content View link shows its current status (the
        environment to which it is published)

    :CaseLevel: Integration
    """
    org = entities.Organization().create()
    lc_env = entities.LifecycleEnvironment(organization=org).create()
    content_view = entities.ContentView(organization=org).create()
    content_view.publish()
    promote(content_view.read().version[0], lc_env.id)
    with session:
        session.organization.select(org_name=org.name)
        cv_values = session.dashboard.read('ContentViews')
        assert content_view.name in cv_values[
            'content_views'][0]['Content View']
        assert cv_values['content_views'][0][
            'Task'] == 'Promoted to {0}'.format(lc_env.name)
        assert 'Success' in cv_values['content_views'][0]['Status']
        assert content_view.name in cv_values[
            'content_views'][1]['Content View']
        assert cv_values['content_views'][1]['Task'] == 'Published new version'
        assert 'Success' in cv_values['content_views'][1]['Status']


@tier2
def test_positive_rendering_after_env_removed(session):
    """Check if Dashboard UI rendered properly after lc environment for
    active organization is removed from the system

    :id: 81c52395-3476-4123-bc3b-49d6c658da9a

    :Steps:

        1. Create an environment (e.g. Dev)
        2. Create a content view and promote it to the environment
        3. Remove the environment.
        4. Visit the dashboard page and verify that it loads successfully.

    :expectedresults: Dashboard search box and necessary widgets are
        rendered before and after necessary environment is removed

    :BZ: 1361793

    :CaseLevel: Integration
    """
    org = entities.Organization().create()
    lc_env = entities.LifecycleEnvironment(organization=org).create()
    content_view = entities.ContentView(organization=org).create()
    content_view.publish()
    promote(content_view.read().version[0], lc_env.id)
    with session:
        session.organization.select(org_name=org.name)
        values = session.dashboard.search('lifecycle_environment={}'.format(
            lc_env.name))
        assert content_view.name in values['ContentViews'][
            'content_views'][0]['Content View']
        entities.LifecycleEnvironment(id=lc_env.id).delete()
        values = session.dashboard.search('lifecycle_environment={}'.format(
            lc_env.name))
        assert values['HostConfigurationStatus']['total_count'] == 0
        assert content_view.name in values['ContentViews'][
            'content_views'][0]['Content View']


@tier2
def test_positive_host_collections(session):
    """Check if the Host Collections widget displays list of host
    collection in UI

    :id: 1feae601-987d-4553-8644-4ceef5059e64

    :Steps:

        1. Make sure to have some hosts and host collections
        2. Navigate Monitor -> Dashboard
        3. Review the Host Collections Widget

    :expectedresults: The list of host collections along with content host
        is displayed in the widget

    :CaseLevel: Integration
    """
    org = entities.Organization().create()
    loc = entities.Location().create()
    host = entities.Host(organization=org, location=loc).create()
    host_collection = entities.HostCollection(
        host=[host], organization=org).create()
    with session:
        session.organization.select(org_name=org.name)
        session.location.select(loc_name=loc.name)
        values = session.dashboard.read('HostCollections')
        assert values['collections'][0]['Name'] == host_collection.name
        assert values['collections'][0]['Content Hosts'] == '1'


@tier2
def test_positive_current_subscription_totals(session):
    """Check if the Current Subscriptions Totals widget is working in the
    Dashboard UI

    :id: 6d0f56ff-7007-4cdb-96f3-d9e8b6cc1701

    :Steps:

        1. Make sure application has some active subscriptions
        2. Navigate to Monitor -> Dashboard
        3. Review the Subscription Status widget

    :expectedresults: The widget displays all the active subscriptions and
        expired subscriptions details

    :CaseLevel: Integration
    """
    org = entities.Organization().create()
    manifests.upload_manifest_locked(org.id)
    with session:
        session.organization.select(org_name=org.name)
        subscription_values = session.dashboard.read('SubscriptionStatus')['subscriptions']
        assert subscription_values[0][
            'Subscription Status'] == 'Active Subscriptions'
        assert int(subscription_values[0]['Count']) >= 1
        assert subscription_values[1][
            'Subscription Status'] == 'Subscriptions Expiring in 120 Days'
        assert int(subscription_values[1]['Count']) == 0
        assert subscription_values[2][
            'Subscription Status'] == 'Recently Expired Subscriptions'
        assert int(subscription_values[2]['Count']) == 0


@tier3
@run_in_one_thread
@skip_if_not_set('clients', 'fake_manifest')
@upgrade
def test_positive_content_host_subscription_status(session):
    """Check if the Content Host Subscription Status is working in the
    Dashboard UI

    :id: ce0d7b0c-ae6a-4361-8173-e50f6381194a

    :Steps:

        1. Register Content Host and subscribe it
        2. Navigate Monitor -> Dashboard
        3. Review the Content Host Subscription Status
        4. Click each link:

            a. Invalid Subscriptions
            b. Valid Subscriptions

    :expectedresults: The widget is updated with all details for Valid,
        and Invalid Subscriptions

    :CaseLevel: System
    """
    org = entities.Organization().create()
    env = entities.LifecycleEnvironment(organization=org).create()
    repos_collection = RepositoryCollection(
        distro=DISTRO_RHEL7,
        repositories=[
            SatelliteToolsRepository(cdn=True),
        ]
    )
    repos_collection.setup_content(org.id, env.id, upload_manifest=True)
    with VirtualMachine(distro=DISTRO_RHEL7) as client:
        repos_collection.setup_virtual_machine(client)
        assert client.subscribed
        with session:
            session.organization.select(org_name=org.name)
            session.dashboard.action({'HostSubscription': {'type': 'Invalid'}})
            values = session.contenthost.read_all()
            assert values['searchbox'] == 'subscription_status = invalid'
            assert len(values['table']) == 0
            session.dashboard.action({'HostSubscription': {'type': 'Valid'}})
            values = session.contenthost.read_all()
            assert values['searchbox'] == 'subscription_status = valid'
            assert len(values['table']) == 1
            assert values['table'][0]['Name'] == client.hostname
            assert values['table'][0]['Lifecycle Environment'] == env.name
            cv_name = repos_collection._setup_content_data[
                'content_view']['name']
            assert values['table'][0]['Content View'] == cv_name


@upgrade
@run_in_one_thread
@skip_if_not_set('clients')
@tier3
def test_positive_user_access_with_host_filter(test_name, module_loc):
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
        default_location=module_loc,
        location=[module_loc],
        role=[role],
        login=user_login,
        password=user_password
    ).create()
    with Session(test_name, user=user_login, password=user_password) as session:
        assert session.dashboard.read('HostConfigurationStatus')['total_count'] == 0
        assert len(session.dashboard.read('LatestErrata')) == 0
        repos_collection = RepositoryCollection(
            distro=DISTRO_RHEL7,
            repositories=[
                SatelliteToolsRepository(),
                YumRepository(url=FAKE_6_YUM_REPO),
            ]
        )
        repos_collection.setup_content(org.id, lce.id)
        with VirtualMachine(distro=repos_collection.distro) as client:
            repos_collection.setup_virtual_machine(client)
            result = client.run('yum install -y {0}'.format(FAKE_1_CUSTOM_PACKAGE))
            assert result.return_code == 0
            hostname = client.hostname
            # Check UI for values
            assert session.host.search(hostname)[0]['Name'] == hostname
            hosts_values = session.dashboard.read('HostConfigurationStatus')
            assert hosts_values['total_count'] == 1
            errata_values = session.dashboard.read('LatestErrata')['erratas']
            assert len(errata_values) == 1
            assert errata_values[0]['Type'] == 'security'
            assert FAKE_2_ERRATA_ID in errata_values[0]['Errata']


@tier2
def test_positive_sync_overview_widget(session):
    """Check if the Sync Overview Widget is working in the Dashboard UI

    :id: 515027f5-19e8-4f83-9042-1c347a63758f

    :Steps:

        1. Create a product
        2. Add a repo and sync it
        3. Navigate to Monitor -> Dashboard
        4. Review the Sync Overview widget for the above sync details

    :expectedresults: Sync Overview widget is updated with all sync processes

    :CaseLevel: Integration
    """
    product_name = gen_string('alpha')
    org = entities.Organization().create()
    create_sync_custom_repo(org.id, product_name=product_name)
    with session:
        session.organization.select(org_name=org.name)
        sync_values = session.dashboard.read('SyncOverview')['syncs']
        assert len(sync_values) == 1
        assert sync_values[0]['Product'] == product_name
        assert sync_values[0]['Status'] == 'Syncing Complete.'
        assert 'ago' in sync_values[0]['Finished']
