"""Test module for Dashboard UI

:Requirement: Dashboard

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import (
    gen_ipaddr,
    gen_mac,
    gen_string
)

from nailgun import entities
from nailgun.entity_mixins import TaskFailedError
from pytest import raises
from requests.exceptions import HTTPError

from robottelo.api.utils import promote
from robottelo.constants import DISTRO_RHEL7
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


@tier2
def test_positive_discovered_host(session):
    """Check if the Discovered Host widget is working in the Dashboard UI

    :id: 74afef58-71f4-49e1-bbb6-6d4355d385f8

    :Steps:

        1. Create a Discovered Host.
        2. Navigate Monitor -> Dashboard
        3. Review the Discovered Host Status.

    :expectedresults: The widget is updated with all details.

    :CaseLevel: Integration
    """
    org = entities.Organization().create()
    loc = entities.Location(organization=[org]).create()
    ipaddress = gen_ipaddr()
    macaddress = gen_mac(multicast=False)
    model = gen_string('alpha', length=5)
    host_name = 'mac{0}'.format(macaddress.replace(':', ''))
    entities.DiscoveredHost().facts(json={
        u'facts': {
            u'name': gen_string('alpha'),
            u'discovery_bootip': ipaddress,
            u'discovery_bootif': macaddress,
            u'interfaces': 'eth0',
            u'ipaddress': ipaddress,
            u'macaddress': macaddress,
            u'macaddress_eth0': macaddress,
            u'ipaddress_eth0': ipaddress,
            u'foreman_organization': org.name,
            u'foreman_location': loc.name,
            u'model': model,
            u'memorysize_mb': 1000,
            u'physicalprocessorcount': 2,
        }
    })

    with session:
        session.organization.select(org_name=org.name)
        session.location.select(loc_name=loc.name)
        values = session.dashboard.read('DiscoveredHosts')
        assert len(values) == 2
        assert values['hosts_count'] == '1 Discovered Host'
        assert values['hosts'][0]['Host'] == host_name
        assert values['hosts'][0]['Model'] == model
        assert values['hosts'][0]['CPUs'] == '2'
        assert values['hosts'][0]['Memory'] == '1000 MB'
