"""
:Requirement: Report templates

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: Reporting

:Assignee: lhellebr

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from broker import VMBroker
from fauxfactory import gen_alpha

from robottelo import manifests
from robottelo.cli.activationkey import ActivationKey
from robottelo.cli.base import Base
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.contentview import ContentView
from robottelo.cli.factory import CLIFactoryError
from robottelo.cli.factory import make_activation_key
from robottelo.cli.factory import make_architecture
from robottelo.cli.factory import make_content_view
from robottelo.cli.factory import make_fake_host
from robottelo.cli.factory import make_filter
from robottelo.cli.factory import make_lifecycle_environment
from robottelo.cli.factory import make_medium
from robottelo.cli.factory import make_org
from robottelo.cli.factory import make_os
from robottelo.cli.factory import make_partition_table
from robottelo.cli.factory import make_product
from robottelo.cli.factory import make_report_template
from robottelo.cli.factory import make_repository
from robottelo.cli.factory import make_role
from robottelo.cli.factory import make_template_input
from robottelo.cli.factory import make_user
from robottelo.cli.factory import setup_org_for_a_custom_repo
from robottelo.cli.factory import setup_org_for_a_rh_repo
from robottelo.cli.filter import Filter
from robottelo.cli.host import Host
from robottelo.cli.location import Location
from robottelo.cli.org import Org
from robottelo.cli.report_template import ReportTemplate
from robottelo.cli.repository import Repository
from robottelo.cli.settings import Settings
from robottelo.cli.subscription import Subscription
from robottelo.cli.user import User
from robottelo.config import settings
from robottelo.constants import DEFAULT_LOC
from robottelo.constants import DEFAULT_ORG
from robottelo.constants import FAKE_0_CUSTOM_PACKAGE_NAME
from robottelo.constants import FAKE_1_CUSTOM_PACKAGE
from robottelo.constants import FAKE_1_CUSTOM_PACKAGE_NAME
from robottelo.constants import FAKE_2_CUSTOM_PACKAGE
from robottelo.constants import PRDS
from robottelo.constants import REPORT_TEMPLATE_FILE
from robottelo.constants import REPOS
from robottelo.constants import REPOSET
from robottelo.hosts import ContentHost
from robottelo.ssh import upload_file


@pytest.fixture(scope='module')
def local_org():
    """Create org with CLI factory and upload cloned manifest"""
    org = make_org()
    with manifests.clone() as manifest:
        upload_file(manifest.content, manifest.filename)
    return org


@pytest.fixture(scope='module')
def local_environment(local_org):
    """Create a lifecycle environment with CLI factory"""
    return make_lifecycle_environment({'organization-id': local_org['id']})


@pytest.fixture(scope='module')
def local_content_view(local_org):
    """Create content view, repository, and product"""
    new_product = make_product({'organization-id': local_org['id']})
    new_repo = make_repository({'product-id': new_product['id']})
    Repository.synchronize({'id': new_repo['id']})
    content_view = make_content_view({'organization-id': local_org['id']})
    ContentView.add_repository(
        {
            'id': content_view['id'],
            'organization-id': local_org['id'],
            'repository-id': new_repo['id'],
        }
    )
    ContentView.publish({'id': content_view['id']})
    return content_view


@pytest.fixture(scope='module')
def local_ak(local_org, local_environment, local_content_view):
    """Promote a content view version and create an activation key with CLI Factory"""
    cvv = ContentView.info({'id': local_content_view['id']})['versions'][0]
    ContentView.version_promote(
        {'id': cvv['id'], 'to-lifecycle-environment-id': local_environment['id']}
    )
    return make_activation_key(
        {
            'lifecycle-environment-id': local_environment['id'],
            'content-view': local_content_view['name'],
            'organization-id': local_org['id'],
            'auto-attach': False,
        }
    )


@pytest.fixture(scope='module')
def local_subscription(local_org, local_ak):
    subscription = Subscription.list({'organization-id': local_org['id']}, per_page=False)[0]
    ActivationKey.add_subscription({'id': local_ak['id'], 'subscription-id': subscription['id']})

    return subscription


@pytest.mark.tier2
def test_positive_report_help():
    """hammer level of help included in test:
     Base level hammer help includes report-templates,
     Command level hammer help contains usage details,
     Subcommand level hammer help contains usage details

    :id: ec395f47-a55f-441a-9cc6-e49400c83e8e

    :setup: Any satellite user

    :steps:

        1. hammer --help
        2. hammer report-template --help
        3. hammer report-template create --help

    :expectedresults: report-templates command is included in help,
                      report-templates command details are displayed,
                      report-templates create command details are displayed

    """
    command_output = '\n'.join(Base().execute('--help'))
    assert 'report-template' in command_output
    command_output = '\n'.join(Base().execute('report-template --help'))
    assert all(
        [
            phrase in command_output
            for phrase in [
                'hammer report-template',
                'info',
                'report template',
                'generate',
                'report',
            ]
        ]
    )
    command_output = '\n'.join(Base().execute('report-template create --help'))
    assert all(
        [
            phrase in command_output
            for phrase in ['hammer report-template create', '--audit-comment', '--interactive']
        ]
    )


@pytest.mark.tier1
def test_positive_end_to_end_crud_and_list():
    """CRUD test + list test for report templates

    :id: 2a143ddf-683f-49e2-badb-f9a387cfc53c

    :setup: User with reporting access rights and following setup:
            create - doesn't require other setup
            list   - at least two report templates
            info   - some report template
            update - some report template that is not locked
            delete - some report template that is not locked

    :steps:

        1. hammer report-template create ...
        2. hammer report-template list ...
        3. hammer report-template info ...
        4. hammer report-template update ... # change some value
        5. hammer report-template delete ...

    :expectedresults: Report is created, report templates are listed,
                      data about report template is showed,
                      report template is updated, and deleted.

    :CaseImportance: Critical
    """
    # create
    name = gen_alpha()
    report_template = make_report_template({'name': name})
    assert report_template['name'] == name

    # list - create second template
    tmp_name = gen_alpha()
    tmp_report_template = make_report_template({'name': tmp_name})
    result_list = ReportTemplate.list()
    assert name in [rt['name'] for rt in result_list]

    # info
    result = ReportTemplate.info({'id': report_template['id']})
    assert name == result['name']

    # update
    new_name = gen_alpha()
    result = ReportTemplate.update({'name': report_template['name'], 'new-name': new_name})
    assert new_name == result[0]['name']
    rt_list = ReportTemplate.list()
    assert name not in [rt['name'] for rt in rt_list]

    # delete tmp
    ReportTemplate.delete({'name': tmp_report_template['name']})
    with pytest.raises(CLIReturnCodeError):
        ReportTemplate.info({'id': tmp_report_template['id']})


@pytest.mark.tier1
def test_positive_generate_report_nofilter_and_with_filter():
    """Generate Host Status report without filter and with filter

    :id: 5af03399-b918-468a-9306-1c76dda6a369

    :setup: User with reporting access rights, some report template, at least two hosts

    :steps:

        0. use default report template called Host - Statuses
        1. hammer report-template generate --id ... # do not specify any filter
        2. hammer report-template generate --id ... # specify filter

    :expectedresults: nofilter - Report is generated for all hosts visible for user
                      filter   - Report is generated for the host specified by the filter

    :CaseImportance: Critical
    """
    host_name = gen_alpha()
    host1 = make_fake_host({'name': host_name})

    host_name_2 = gen_alpha()
    host2 = make_fake_host({'name': host_name_2})

    result_list = ReportTemplate.list()
    assert 'Host - Statuses' in [rt['name'] for rt in result_list]

    rt_host_statuses = ReportTemplate.info({'name': 'Host - Statuses'})
    result_no_filter = ReportTemplate.generate({'name': rt_host_statuses['name']})

    assert host1['name'] in [item.split(',')[0] for item in result_no_filter]
    assert host2['name'] in [item.split(',')[0] for item in result_no_filter]

    result = ReportTemplate.generate(
        {
            'name': rt_host_statuses['name'],
            'inputs': (
                rt_host_statuses['template-inputs'][0]['name'] + '=' + f'name={host1["name"]}'
            ),
        }
    )
    assert host1['name'] in [item.split(',')[0] for item in result]
    assert host2['name'] not in [item.split(',')[0] for item in result]


@pytest.mark.tier2
def test_positive_lock_and_unlock_report():
    """Lock and unlock report template

    :id: df306515-8798-4ce3-9430-6bc3bf9b9b33

    :setup: User with reporting access rights, some report template that is not locked

    :steps:

        1. hammer report-template update ... --locked true
        2. hammer report-template update ... --locked false

    :expectedresults: Report is locked and unlocked successfully.

    :CaseImportance: Medium
    """
    name = gen_alpha()
    report_template = make_report_template({'name': name})
    ReportTemplate.update({'name': report_template['name'], 'locked': 1})
    new_name = gen_alpha()
    with pytest.raises(CLIReturnCodeError):
        ReportTemplate.update({'name': report_template['name'], 'new-name': new_name})

    ReportTemplate.update({'name': report_template['name'], 'locked': 0})
    result = ReportTemplate.update({'name': report_template['name'], 'new-name': new_name})
    assert result[0]['name'] == new_name


@pytest.mark.tier2
def test_positive_report_add_userinput():
    """Add user input to template

    :id: 84b577db-144e-4761-a46e-e83887464986

    :setup: User with reporting access rights

    :steps:

        1. hammer template-input create ...

    :expectedresults: User input is assigned to the report template

    """
    name = gen_alpha()
    report_template = make_report_template({'name': name})
    ti_name = gen_alpha()
    template_input = make_template_input(
        {'name': ti_name, 'input-type': 'user', 'template-id': report_template['id']}
    )
    result = ReportTemplate.info({'name': report_template['name']})
    assert result['template-inputs'][0]['name'] == template_input['name']


@pytest.mark.tier2
def test_positive_dump_report():
    """Export report template

    :id: 84b577db-144e-4761-a42e-a83887464986

    :setup: User with reporting access rights, some report template

    :steps:

        1. hammer report-template dump ...

    :expectedresults: Report script is shown

    :CaseImportance: Medium
    """
    name = gen_alpha()
    content = gen_alpha()
    report_template = make_report_template({'name': name, 'content': content})
    result = ReportTemplate.dump({'id': report_template['id']})
    assert content in result


@pytest.mark.tier2
def test_positive_clone_locked_report():
    """Clone locked report template

    :id: cc843731-b9c2-4fc9-9e15-d1ee5d967cda

    :setup: User with reporting access rights, some report template that is locked

    :steps:

        1. hammer report-template clone ...

    :expectedresults: Report is cloned

    :CaseImportance: Medium
    """

    name = gen_alpha()
    report_template = make_report_template({'name': name})
    ReportTemplate.update({'name': report_template['name'], 'locked': 1, 'default': 1})
    new_name = gen_alpha()
    ReportTemplate.clone({'id': report_template['id'], 'new-name': new_name})
    result_list = ReportTemplate.list()
    assert new_name in [rt['name'] for rt in result_list]
    result_info = ReportTemplate.info({'id': report_template['id']})
    assert result_info['locked'] == 'yes'
    assert result_info['default'] == 'yes'


@pytest.mark.tier2
def test_positive_generate_report_sanitized():
    """Generate report template where there are values in comma outputted
    which might brake CSV format

    :id: 84b577db-144e-4961-a42e-e93887464986

    :setup: User with reporting access rights, Host Statuses report,
            a host with OS that has comma in its name

    :steps:

        1. hammer report-template generate ...

    :expectedresults: Report is generated in proper CSV format (value with comma is quoted)

    :CaseImportance: Medium
    """
    # create a name that has a comma in it, some randomized text, and no spaces.
    os_name = gen_alpha(start='test', separator=',').replace(' ', '')
    architecture = make_architecture()
    partition_table = make_partition_table()
    medium = make_medium()
    os = make_os(
        {
            'name': os_name,
            'architecture-ids': architecture['id'],
            'medium-ids': medium['id'],
            'partition-table-ids': partition_table['id'],
        }
    )

    host_name = gen_alpha()
    host = make_fake_host(
        {
            'name': host_name,
            'architecture-id': architecture['id'],
            'medium-id': medium['id'],
            'operatingsystem-id': os['id'],
            'partition-table-id': partition_table['id'],
        }
    )

    report_template = make_report_template({'content': REPORT_TEMPLATE_FILE})

    result = ReportTemplate.generate({'name': report_template['name']})
    assert 'Name,Operating System' in result  # verify header of custom template
    assert f'{host["name"]},"{host["operating-system"]["operating-system"]}"' in result


@pytest.mark.tier3
@pytest.mark.stubbed
def test_positive_applied_errata():
    """Generate an Applied Errata report, then generate it by using schedule --wait and then
    use schedule and report-data to download generated Applied Errata report,
    this test use same resources (time saving) to test generate, schedule and report-data
    functionality

    :id: 780ac7a9-e3fe-44d1-8af7-687816debe9b

    :setup: User with reporting access rights, some host with applied errata

    :steps:

        1. hammer report-template generate ...

        2. hammer report-template schedule --wait ...

        3.1 hammer report-template schedule ...
        3.2 hammer report-template report-data --job-id= ...

    :expectedresults: 1. A report is generated with all applied errata listed
                      2,3. A report is generated asynchronously

    """


@pytest.mark.tier2
@pytest.mark.stubbed
def test_positive_generate_email_compressed():
    """Generate an Applied Errata report, get it by e-mail, compressed

    :id: a4b877db-143e-4871-a42e-e93887464986

    :setup: User with reporting access rights, some host with applied errata

    :steps:

        1. hammer report-template schedule ...

    :expectedresults: A report is generated asynchronously, the result
                      is compressed and mailed to the specified address

    :CaseImportance: Medium
    """


@pytest.mark.tier2
@pytest.mark.stubbed
def test_positive_generate_email_uncompressed():
    """Generate an Applied Errata report, get it by e-mail, uncompressed

    :id: a4b977db-143f-4871-a42e-e93887464986

    :setup: User with reporting access rights, some host with applied errata

    :steps:

        1. hammer report-template schedule ...

    :expectedresults: A report is generated asynchronously, the result
                      is not compressed and is mailed
                      to the specified address

    :CaseImportance: Medium
    """


@pytest.mark.tier2
def test_negative_create_report_without_name():
    """Try to create a report template with empty name

    :id: 84b577db-144e-4771-a42e-e93887464986

    :setup: User with reporting access rights

    :steps:

        1. hammer report-template create --name '' ...

    :expectedresults: Report is not created

    :CaseImportance: Medium
    """
    with pytest.raises(CLIFactoryError):
        make_report_template({'name': ''})


@pytest.mark.tier2
def test_negative_delete_locked_report():
    """Try to delete a locked report template

    :id: 84b577db-144e-4871-a42e-e93887464986

    :setup: User with reporting access rights, some report template that is locked

    :steps:

        1. hammer report-template delete ...

    :expectedresults: Report is not deleted

    :CaseImportance: Medium
    """
    name = gen_alpha()
    report_template = make_report_template({'name': name})

    ReportTemplate.update({'name': report_template['name'], 'locked': 1})

    with pytest.raises(CLIReturnCodeError):
        ReportTemplate.delete({'name': report_template['name']})


@pytest.mark.tier2
def test_negative_bad_email():
    """Report can't be generated when incorrectly formed mail specified

    :id: a4ba77db-144e-4871-a42e-e93887464986

    :setup: User with reporting access rights, some host with applied errata

    :steps:

        1. hammer report-template schedule ...

    :expectedresults: Error message about wrong e-mail address, no task is triggered

    :CaseImportance: Medium
    """
    name = gen_alpha()
    report_template = make_report_template({'name': name})

    with pytest.raises(CLIReturnCodeError):
        ReportTemplate.schedule({'name': report_template['name'], 'mail-to': gen_alpha()})


@pytest.mark.tier3
def test_negative_nonauthor_of_report_cant_download_it():
    """The resulting report should only be downloadable by
       the user that generated it or admin. Check.

    :id: a4bc77db-146e-4871-a42e-e93887464986

    :setup: Installed Satellite, user that can list running tasks

    :steps:

        1. hammer -u u1 -p p1 report-template schedule
        2. hammer -u u2 -p p2 report-template report-data

    :expectedresults: Report can't be downloaded. Error.
    """
    uname_viewer = gen_alpha()
    uname_viewer2 = gen_alpha()
    password = gen_alpha()

    loc = Location.info({'name': DEFAULT_LOC})
    org = Org.info({'name': DEFAULT_ORG})

    user1 = make_user(
        {
            'login': uname_viewer,
            'password': password,
            'organization-ids': org['id'],
            'location-ids': loc['id'],
        }
    )

    user2 = make_user(
        {
            'login': uname_viewer2,
            'password': password,
            'organization-ids': org['id'],
            'location-ids': loc['id'],
        }
    )

    role = make_role()
    # Pick permissions by its resource type
    permissions_org = [
        permission['name']
        for permission in Filter.available_permissions({'search': 'resource_type=Organization'})
    ]
    permissions_loc = [
        permission['name']
        for permission in Filter.available_permissions({'search': 'resource_type=Location'})
    ]
    permissions_rt = [
        permission['name']
        for permission in Filter.available_permissions({'search': 'resource_type=ReportTemplate'})
    ]
    permissions_pt = [
        permission['name']
        for permission in Filter.available_permissions(
            {'search': 'resource_type=ProvisioningTemplate'}
        )
    ]
    permissions_jt = [
        permission['name']
        for permission in Filter.available_permissions({'search': 'resource_type=JobTemplate'})
    ]
    # Assign filters to created role
    for perm in [permissions_org, permissions_loc, permissions_rt, permissions_pt, permissions_jt]:
        make_filter({'role-id': role['id'], 'permissions': perm})
    User.add_role({'login': user1['login'], 'role-id': role['id']})
    User.add_role({'login': user2['login'], 'role-id': role['id']})

    name = gen_alpha()
    content = gen_alpha()

    report_template = ReportTemplate.with_user(username=user1['login'], password=password).create(
        {'name': name, 'organization-id': org['id'], 'location-id': loc['id'], 'file': content}
    )

    schedule = ReportTemplate.with_user(username=user1['login'], password=password).schedule(
        {'name': report_template['name']}
    )

    report_data = ReportTemplate.with_user(username=user1['login'], password=password).report_data(
        {'id': report_template['name'], 'job-id': schedule[0].split('Job ID: ', 1)[1]}
    )

    assert content in report_data
    with pytest.raises(CLIReturnCodeError):
        ReportTemplate.with_user(username=user2['login'], password=password).report_data(
            {'id': report_template['name'], 'job-id': schedule[0].split('Job ID: ', 1)[1]}
        )


@pytest.mark.tier2
@pytest.mark.skip_if_open('BZ:1750924')
def test_positive_generate_with_name_and_org():
    """Generate Host Status report, specifying template name and organization

    :id: 5af03399-b918-468a-1306-1c76dda6f369

    :setup: User with reporting access rights, some report template, some host

    :steps:

        0. use default report template called Host - Statuses
        1. hammer report-template generate --name ... --organization ...

    :expectedresults: Report successfully generated (in BZ, it results in
        "ERF42-5227 [Foreman::Exception]: unknown parent permission for
        api/v2/report_templates#generate")

    :CaseImportance: Medium

    :BZ: 1750924
    """
    host_name = gen_alpha()
    host = make_fake_host({'name': host_name})

    result = ReportTemplate.generate({'name': 'Host - Statuses', 'organization': DEFAULT_ORG})

    assert host['name'] in [item.split(',')[0] for item in result]


@pytest.mark.tier2
@pytest.mark.skip_if_open('BZ:1782807')
def test_positive_generate_ansible_template():
    """Report template named 'Ansible Inventory' (default name is specified in settings)
    must be present in Satellite 6.7 and later in order to provide enhanced functionality
    for Ansible Tower inventory synchronization with Satellite.

    :id: f1f7adfc-9601-4498-95c8-3e82e2b36583

    :setup:
        1. A user with minimal required permissions: 'Ansible Tower Inventory Reader' role
        2. A fake host to be checked in report output

    :steps:
        1. Check settings for default Ansible Inventory template name and ensure
           the template is present
        2. Try to render the template using the user with ATIR role
        3. Check the fake host is present in the output

    :expectedresults: Report template is present, renederable and provides output

    :CaseImportance: Medium
    """
    settings = Settings.list({'search': 'name=ansible_inventory_template'})
    assert 1 == len(settings)
    template_name = settings[0]['value']

    report_list = ReportTemplate.list()
    assert template_name in [rt['name'] for rt in report_list]

    login = gen_alpha().lower()
    password = gen_alpha().lower()
    loc = Location.info({'name': DEFAULT_LOC})
    org = Org.info({'name': DEFAULT_ORG})

    user = make_user(
        {
            'login': login,
            'password': password,
            'organization-ids': org['id'],
            'location-ids': loc['id'],
        }
    )

    User.add_role({'login': user['login'], 'role': 'Ansible Tower Inventory Reader'})

    host_name = gen_alpha().lower()
    host = make_fake_host({'name': host_name})

    schedule = ReportTemplate.with_user(username=user['login'], password=password).schedule(
        {'name': template_name}
    )

    report_data = ReportTemplate.with_user(username=user['login'], password=password).report_data(
        {'name': template_name, 'job-id': schedule[0].split('Job ID: ', 1)[1]}
    )

    assert host['name'] in [item.split(',')[1] for item in report_data if len(item) > 0]


@pytest.mark.tier3
def test_positive_generate_entitlements_report_multiple_formats(
    local_org, local_ak, local_subscription, rhel7_contenthost
):
    """Generate an report using the Subscription - Entitlement Report template
    in html, yaml, and csv format.

    :id: f2b74916-1298-4d20-9c24-a2c2b3a3e9a9

    :setup: Installed Satellite with Organization, Activation key,
            Content View, Content Host, and Subscriptions.

    :steps:
        1. hammer report-template generate --organization '' --id '' --report-format ''

    :expectedresults: report is generated containing all the expected information
                      regarding entitlements.

    :BZ: 1830289
    """
    client = rhel7_contenthost
    client.install_katello_ca()
    client.register_contenthost(local_org['label'], local_ak['name'])
    assert client.subscribed
    result_html = ReportTemplate.generate(
        {
            'organization': local_org['name'],
            'name': 'Subscription - Entitlement Report',
            'report-format': 'html',
            'inputs': 'Days from Now=no limit',
        }
    )
    assert client.hostname in result_html[2]
    assert local_subscription['name'] in result_html[2]
    result_yaml = ReportTemplate.generate(
        {
            'organization': local_org['name'],
            'name': 'Subscription - Entitlement Report',
            'report-format': 'yaml',
            'inputs': 'Days from Now=no limit',
        }
    )
    for entry in result_yaml:
        if '-Name:' in entry:
            assert client.hostname in entry
        elif 'Subscription Name:' in entry:
            assert local_subscription['name'] in entry
    result_csv = ReportTemplate.generate(
        {
            'organization': local_org['name'],
            'name': 'Subscription - Entitlement Report',
            'report-format': 'csv',
            'inputs': 'Days from Now=no limit',
        }
    )
    assert client.hostname in result_csv[1]
    assert local_subscription['name'] in result_csv[1]
    # BZ 1830289
    assert 'Subscription Quantity' in result_csv[0]


@pytest.mark.tier3
def test_positive_schedule_entitlements_report(
    local_org, local_ak, local_subscription, rhel7_contenthost
):
    """Schedule an report using the Subscription - Entitlement Report template in csv format.

    :id: 572fb387-86e0-40e2-b2df-e8ec26433610


    :setup: Installed Satellite with Organization, Activation key,
            Content View, Content Host, and Subscriptions.

    :steps:
        1. hammer report-template schedule --organization '' --id '' --report-format ''


    :expectedresults: report is scheduled and generated containing all the expected information
                      regarding entitlements.
    """
    client = rhel7_contenthost
    client.install_katello_ca()
    client.register_contenthost(local_org['label'], local_ak['name'])
    assert client.subscribed
    scheduled_csv = ReportTemplate.schedule(
        {
            'name': 'Subscription - Entitlement Report',
            'organization': local_org['name'],
            'report-format': 'csv',
            'inputs': 'Days from Now=no limit',
        }
    )
    data_csv = ReportTemplate.report_data(
        {
            'name': 'Subscription - Entitlement Report',
            'job-id': scheduled_csv[0].split('Job ID: ', 1)[1],
        }
    )
    assert any(client.hostname in line for line in data_csv)
    assert any(local_subscription['name'] in line for line in data_csv)


@pytest.mark.tier3
def test_positive_generate_hostpkgcompare(
    local_org, local_ak, local_content_view, local_environment
):
    """Generate 'Host - compare content hosts packages' report

    :id: 572fb387-86f2-40e2-b2df-e8ec26433610


    :setup: Installed Satellite with Organization, Activation key,
            Content View, Content Host, Subscriptions, and synced fake repo.

    :steps:
        1. hammer report-template generate --name 'Host - compare content hosts package' ...

    :expectedresults: report is scheduled and generated containing all the expected information
                      regarding host packages

    :CaseImportance: Medium

    :BZ: 1860430
    """
    # Add subscription to Satellite Tools repo to activation key
    setup_org_for_a_rh_repo(
        {
            'product': PRDS['rhel'],
            'repository-set': REPOSET['rhst7'],
            'repository': REPOS['rhst7']['name'],
            'organization-id': local_org['id'],
            'content-view-id': local_content_view['id'],
            'lifecycle-environment-id': local_environment['id'],
            'activationkey-id': local_ak['id'],
        }
    )
    setup_org_for_a_custom_repo(
        {
            'url': settings.repos.yum_6.url,
            'organization-id': local_org['id'],
            'content-view-id': local_content_view['id'],
            'lifecycle-environment-id': local_environment['id'],
            'activationkey-id': local_ak['id'],
        }
    )

    hosts_info = []
    with VMBroker(nick='rhel7', host_classes={'host': ContentHost}, _count=2) as hosts:
        for client in hosts:
            # Create RHEL hosts via broker and register content host
            client.install_katello_ca()
            # Register content host, install katello-agent
            client.register_contenthost(local_org['label'], local_ak['name'])
            assert client.subscribed
            hosts_info.append(Host.info({'name': client.hostname}))
            client.enable_repo(REPOS['rhst7']['id'])
            client.install_katello_agent()
        hosts_info.sort(key=lambda host: host['name'])

        host1, host2 = hosts_info
        Host.package_install({'host-id': host1['id'], 'packages': FAKE_0_CUSTOM_PACKAGE_NAME})
        Host.package_install({'host-id': host1['id'], 'packages': FAKE_1_CUSTOM_PACKAGE})
        Host.package_install({'host-id': host2['id'], 'packages': FAKE_2_CUSTOM_PACKAGE})

        result = ReportTemplate.generate(
            {
                'name': 'Host - compare content hosts packages',
                'inputs': f'Host 1 = {host1["name"]}, ' f'Host 2 = {host2["name"]}',
            }
        )
        result.remove('')

        assert len(result) > 1
        headers = f'Package,{host1["name"]},{host2["name"]},Architecture,Status'
        assert headers == result[0]
        items = [item.split(',') for item in result[1:]]
        assert len(items)
        for item in items:
            assert len(item) == 5
            name, host1version, host2version, arch, status = item
            assert len(name)
            assert (
                (host1version == '-' and name in host2version)
                or (name in host1version and host2version == '-')
                or (name in host1version and name in host2version)
            )
            assert arch in ['x86_64', 'i686', 's390x', 'ppc64', 'ppc64le', 'noarch']
            assert status in (
                'same version',
                f'{host1["name"]} only',
                f'{host2["name"]} only',
                f'lower in {host1["name"]}',
                f'greater in {host1["name"]}',
            )
            # test for specific installed packages
            if name == FAKE_0_CUSTOM_PACKAGE_NAME:
                assert status == f'{host1["name"]} only'
            if name == FAKE_1_CUSTOM_PACKAGE_NAME:
                assert (
                    status == f'lower in {host1["name"]}' or status == f'greater in {host2["name"]}'
                )


@pytest.mark.tier3
def test_negative_generate_hostpkgcompare_nonexistent_host():
    """Try to generate 'Host - compare content hosts packages' report
    with nonexistent hosts inputs

    :id: 572fb387-86e0-40e2-b2df-ef5c26433610

    :setup: Installed Satellite

    :steps:
        1. hammer report-template generate --name 'Host - compare content hosts packages'
           --inputs 'Host 1 = nonexistent1, Host 2 = nonexistent2'

    :expectedresults: report is not generated, sane error shown

    :CaseImportance: Medium

    :BZ: 1860351
    """
    with pytest.raises(CLIReturnCodeError) as cm:
        ReportTemplate.generate(
            {
                'name': 'Host - compare content hosts packages',
                'inputs': 'Host 1 = nonexistent1, ' 'Host 2 = nonexistent2',
            }
        )
        assert "At least one of the hosts couldn't be found" in cm.exception.stderr
