"""
:Requirement: Report templates

:CaseAutomation: Automated

:CaseComponent: Reporting

:team: Endeavour

:CaseImportance: High

"""

from broker import Broker
from fauxfactory import gen_alpha
import pytest

from robottelo.config import settings
from robottelo.constants import (
    DEFAULT_LOC,
    DEFAULT_ORG,
    FAKE_0_CUSTOM_PACKAGE_NAME,
    FAKE_1_CUSTOM_PACKAGE,
    FAKE_1_CUSTOM_PACKAGE_NAME,
    FAKE_2_CUSTOM_PACKAGE,
    PRDS,
    REPORT_TEMPLATE_FILE,
    REPOS,
    REPOSET,
)
from robottelo.exceptions import CLIFactoryError, CLIReturnCodeError
from robottelo.hosts import ContentHost


@pytest.fixture(scope='module')
def local_environment(module_sca_manifest_org, module_target_sat):
    """Create a lifecycle environment with CLI factory"""
    return module_target_sat.cli_factory.make_lifecycle_environment(
        {'organization-id': module_sca_manifest_org.id}
    )


@pytest.fixture(scope='module')
def local_content_view(module_sca_manifest_org, module_target_sat):
    """Create content view, repository, and product"""
    new_product = module_target_sat.cli_factory.make_product(
        {'organization-id': module_sca_manifest_org.id}
    )
    new_repo = module_target_sat.cli_factory.make_repository({'product-id': new_product['id']})
    module_target_sat.cli.Repository.synchronize({'id': new_repo['id']})
    content_view = module_target_sat.cli_factory.make_content_view(
        {'organization-id': module_sca_manifest_org.id}
    )
    module_target_sat.cli.ContentView.add_repository(
        {
            'id': content_view['id'],
            'organization-id': module_sca_manifest_org.id,
            'repository-id': new_repo['id'],
        }
    )
    module_target_sat.cli.ContentView.publish({'id': content_view['id']})
    return content_view


@pytest.fixture(scope='module')
def local_ak(module_sca_manifest_org, local_environment, local_content_view, module_target_sat):
    """Promote a content view version and create an activation key with CLI Factory"""
    cvv = module_target_sat.cli.ContentView.info({'id': local_content_view['id']})['versions'][0]
    module_target_sat.cli.ContentView.version_promote(
        {'id': cvv['id'], 'to-lifecycle-environment-id': local_environment['id']}
    )
    return module_target_sat.cli_factory.make_activation_key(
        {
            'lifecycle-environment-id': local_environment['id'],
            'content-view': local_content_view['name'],
            'organization-id': module_sca_manifest_org.id,
            'auto-attach': False,
        }
    )


def test_positive_report_help(module_target_sat):
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
    command_output = module_target_sat.cli.Base().execute('--help')
    assert 'report-template' in command_output
    command_output = module_target_sat.cli.Base().execute('report-template --help')
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
    command_output = module_target_sat.cli.Base().execute('report-template create --help')
    assert all(
        [
            phrase in command_output
            for phrase in ['hammer report-template create', '--audit-comment', '--interactive']
        ]
    )


@pytest.mark.e2e
def test_positive_end_to_end_crud_and_list(target_sat):
    """CRUD test + list test for report templates

    :id: 2a143ddf-683f-49e2-badb-f9a387cfc53c

    :setup: User with reporting access rights and following setup:
            create - doesn't require other setup
            list   - at least two report templates
            info   - some report template
            update - some report template that is not locked
            clone - some report template
            delete - some report template that is not locked

    :steps:

        1. hammer report-template create ...
        2. hammer report-template list ...
        3. hammer report-template info ...
        4. hammer report-template update ... # change some value
        5. hammer report-template clone ...
        6. hammer report-template delete ...

    :expectedresults: Report is created, report templates are listed,
                      data about report template is showed,
                      report template is updated, report template is cloned, and deleted.

    :CaseImportance: Critical
    """
    # create
    name = gen_alpha()
    report_template = target_sat.cli_factory.report_template({'name': name})
    assert report_template['name'] == name

    # list - create second template
    tmp_name = gen_alpha()
    tmp_report_template = target_sat.cli_factory.report_template({'name': tmp_name})
    result_list = target_sat.cli.ReportTemplate.list()
    assert name in [rt['name'] for rt in result_list]

    # info
    result = target_sat.cli.ReportTemplate.info({'id': report_template['id']})
    assert name == result['name']

    # update
    new_name = gen_alpha()
    result = target_sat.cli.ReportTemplate.update(
        {'name': report_template['name'], 'new-name': new_name}
    )
    assert new_name == result[0]['name']
    rt_list = target_sat.cli.ReportTemplate.list()
    assert name not in [rt['name'] for rt in rt_list]

    # clone
    clone_name = gen_alpha()
    target_sat.cli.ReportTemplate.clone({'id': report_template['id'], 'new-name': clone_name})
    clone_list = target_sat.cli.ReportTemplate.list()
    assert clone_name in [rt['name'] for rt in clone_list]

    # delete tmp
    target_sat.cli.ReportTemplate.delete({'name': tmp_report_template['name']})
    with pytest.raises(CLIReturnCodeError):
        target_sat.cli.ReportTemplate.info({'id': tmp_report_template['id']})


@pytest.mark.parametrize(
    'content',
    [
        '''<% load_users(joins: "LEFT JOIN hosts ON 1=1", select: 'hosts.name AS login,hosts.id AS id', limit: 100_000).each_record do |h| %>
<%= h.id %> - <%= h.login %>
<% end %>
    ''',
        '''<% load_users(joins: ["LEFT JOIN hosts ON 1=1"], select: ['hosts.name AS login,hosts.id AS id'],limit: 100_000).each_record do |h| %>
<%= h.id %> - <%= h.login %>
<% end %>''',
    ],
    ids=['v1', 'v2'],
)
def test_positive_generate_report_check_for_injection(
    module_target_sat, module_org, module_location, content
):
    """Generate a report and check for injection as per CVE-2024-8553

    :id: 1126640e-2eee-4476-aa51-cb473096cbd8

    :setup:
        0. Create a report template containing an exploit

    :steps:
        0. hammer report-template generate --id ...

    :expectedresults:
        Failure with a correct error message

    :CaseImportance: Critical
    """
    name = gen_alpha()
    module_target_sat.cli.ReportTemplate.create(
        {
            'name': name,
            'organization-id': module_org.id,
            'location-id': module_location.id,
            'file': content,
        }
    )

    with pytest.raises(CLIReturnCodeError) as error:
        module_target_sat.cli.ReportTemplate.generate({'name': name})
    assert (
        "Generating Report template failed for: Value of 'select' passed to load_users must be Symbol or Array of Symbols."
        in error.value.stderr
    )


def test_positive_generate_report_nofilter_and_with_filter(module_target_sat):
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
    host1 = module_target_sat.cli_factory.make_fake_host({'name': host_name})

    host_name_2 = gen_alpha()
    host2 = module_target_sat.cli_factory.make_fake_host({'name': host_name_2})

    result_list = module_target_sat.cli.ReportTemplate.list()
    assert 'Host - Statuses' in [rt['name'] for rt in result_list]

    rt_host_statuses = module_target_sat.cli.ReportTemplate.info({'name': 'Host - Statuses'})
    result_no_filter = module_target_sat.cli.ReportTemplate.generate(
        {'name': rt_host_statuses['name']}
    )

    assert host1['name'] in [item.split(',')[0] for item in result_no_filter.splitlines()]
    assert host2['name'] in [item.split(',')[0] for item in result_no_filter.splitlines()]

    result = module_target_sat.cli.ReportTemplate.generate(
        {
            'name': rt_host_statuses['name'],
            'inputs': (
                rt_host_statuses['template-inputs'][0]['name'] + '=' + f'name={host1["name"]}'
            ),
        }
    )
    assert host1['name'] in [item.split(',')[0] for item in result.splitlines()]
    assert host2['name'] not in [item.split(',')[0] for item in result.splitlines()]


def test_positive_lock_and_unlock_report(module_target_sat):
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
    report_template = module_target_sat.cli_factory.report_template({'name': name})
    module_target_sat.cli.ReportTemplate.update({'name': report_template['name'], 'locked': 1})
    new_name = gen_alpha()
    with pytest.raises(CLIReturnCodeError):
        module_target_sat.cli.ReportTemplate.update(
            {'name': report_template['name'], 'new-name': new_name}
        )

    module_target_sat.cli.ReportTemplate.update({'name': report_template['name'], 'locked': 0})
    result = module_target_sat.cli.ReportTemplate.update(
        {'name': report_template['name'], 'new-name': new_name}
    )
    assert result[0]['name'] == new_name


def test_positive_report_add_userinput(module_target_sat):
    """Add user input to template

    :id: 84b577db-144e-4761-a46e-e83887464986

    :setup: User with reporting access rights

    :steps:

        1. hammer template-input create ...

    :expectedresults: User input is assigned to the report template
    """
    name = gen_alpha()
    report_template = module_target_sat.cli_factory.report_template({'name': name})
    ti_name = gen_alpha()
    template_input = module_target_sat.cli_factory.template_input(
        {'name': ti_name, 'input-type': 'user', 'template-id': report_template['id']}
    )
    result = module_target_sat.cli.ReportTemplate.info({'name': report_template['name']})
    assert result['template-inputs'][0]['name'] == template_input['name']


def test_positive_dump_report(module_target_sat):
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
    report_template = module_target_sat.cli_factory.report_template({'name': name, 'file': content})
    result = module_target_sat.cli.ReportTemplate.dump({'id': report_template['id']})
    assert content in result


def test_positive_clone_locked_report(module_target_sat):
    """Clone locked report template

    :id: cc843731-b9c2-4fc9-9e15-d1ee5d967cda

    :setup: User with reporting access rights, some report template that is locked

    :steps:

        1. hammer report-template clone ...

    :expectedresults: Report is cloned

    :CaseImportance: Medium
    """

    name = gen_alpha()
    report_template = module_target_sat.cli_factory.report_template({'name': name})
    module_target_sat.cli.ReportTemplate.update(
        {'name': report_template['name'], 'locked': 1, 'default': 1}
    )
    new_name = gen_alpha()
    module_target_sat.cli.ReportTemplate.clone({'id': report_template['id'], 'new-name': new_name})
    result_list = module_target_sat.cli.ReportTemplate.list()
    assert new_name in [rt['name'] for rt in result_list]
    result_info = module_target_sat.cli.ReportTemplate.info({'id': report_template['id']})
    assert result_info['locked'] == 'yes'
    assert result_info['default'] == 'yes'


def test_positive_generate_report_sanitized(module_target_sat):
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
    architecture = module_target_sat.cli_factory.make_architecture()
    partition_table = module_target_sat.cli_factory.make_partition_table()
    medium = module_target_sat.cli_factory.make_medium()
    os = module_target_sat.cli_factory.make_os(
        {
            'name': os_name,
            'architecture-ids': architecture['id'],
            'medium-ids': medium['id'],
            'partition-table-ids': partition_table['id'],
        }
    )

    host_name = gen_alpha()
    host = module_target_sat.cli_factory.make_fake_host(
        {
            'name': host_name,
            'architecture-id': architecture['id'],
            'medium-id': medium['id'],
            'operatingsystem-id': os['id'],
            'partition-table-id': partition_table['id'],
        }
    )

    report_template = module_target_sat.cli_factory.report_template({'file': REPORT_TEMPLATE_FILE})

    result = module_target_sat.cli.ReportTemplate.generate({'name': report_template['name']})
    assert 'Name,Operating System' in result  # verify header of custom template
    assert f'{host["name"]},"{host["operating-system"]["operating-system"]["name"]}"' in result


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


def test_negative_create_report_without_name(module_target_sat):
    """Try to create a report template with empty name

    :id: 84b577db-144e-4771-a42e-e93887464986

    :setup: User with reporting access rights

    :steps:

        1. hammer report-template create --name '' ...

    :expectedresults: Report is not created

    :CaseImportance: Medium
    """
    with pytest.raises(CLIFactoryError):
        module_target_sat.cli_factory.report_template({'name': ''})


def test_negative_delete_locked_report(module_target_sat):
    """Try to delete a locked report template

    :id: 84b577db-144e-4871-a42e-e93887464986

    :setup: User with reporting access rights, some report template that is locked

    :steps:

        1. hammer report-template delete ...

    :expectedresults: Report is not deleted

    :CaseImportance: Medium
    """
    name = gen_alpha()
    report_template = module_target_sat.cli_factory.report_template({'name': name})

    module_target_sat.cli.ReportTemplate.update({'name': report_template['name'], 'locked': 1})

    with pytest.raises(CLIReturnCodeError):
        module_target_sat.cli.ReportTemplate.delete({'name': report_template['name']})


def test_negative_bad_email(module_target_sat):
    """Report can't be generated when incorrectly formed mail specified

    :id: a4ba77db-144e-4871-a42e-e93887464986

    :setup: User with reporting access rights, some host with applied errata

    :steps:

        1. hammer report-template schedule ...

    :expectedresults: Error message about wrong e-mail address, no task is triggered

    :CaseImportance: Medium
    """
    name = gen_alpha()
    report_template = module_target_sat.cli_factory.report_template({'name': name})

    with pytest.raises(CLIReturnCodeError):
        module_target_sat.cli.ReportTemplate.schedule(
            {'name': report_template['name'], 'mail-to': gen_alpha()}
        )


def test_negative_nonauthor_of_report_cant_download_it(module_target_sat):
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

    loc = module_target_sat.cli.Location.info({'name': DEFAULT_LOC})
    org = module_target_sat.cli.Org.info({'name': DEFAULT_ORG})

    user1 = module_target_sat.cli_factory.user(
        {
            'login': uname_viewer,
            'password': password,
            'organization-ids': org['id'],
            'location-ids': loc['id'],
        }
    )

    user2 = module_target_sat.cli_factory.user(
        {
            'login': uname_viewer2,
            'password': password,
            'organization-ids': org['id'],
            'location-ids': loc['id'],
        }
    )

    role = module_target_sat.cli_factory.make_role()
    # Pick permissions by its resource type
    permissions_org = [
        permission['name']
        for permission in module_target_sat.cli.Filter.available_permissions(
            {'search': 'resource_type=Organization'}
        )
    ]
    permissions_loc = [
        permission['name']
        for permission in module_target_sat.cli.Filter.available_permissions(
            {'search': 'resource_type=Location'}
        )
    ]
    permissions_rt = [
        permission['name']
        for permission in module_target_sat.cli.Filter.available_permissions(
            {'search': 'resource_type=ReportTemplate'}
        )
    ]
    permissions_pt = [
        permission['name']
        for permission in module_target_sat.cli.Filter.available_permissions(
            {'search': 'resource_type=ProvisioningTemplate'}
        )
    ]
    permissions_jt = [
        permission['name']
        for permission in module_target_sat.cli.Filter.available_permissions(
            {'search': 'resource_type=JobTemplate'}
        )
    ]
    # Assign filters to created role
    for perm in [permissions_org, permissions_loc, permissions_rt, permissions_pt, permissions_jt]:
        module_target_sat.cli_factory.make_filter({'role-id': role['id'], 'permissions': perm})
    module_target_sat.cli.User.add_role({'login': user1['login'], 'role-id': role['id']})
    module_target_sat.cli.User.add_role({'login': user2['login'], 'role-id': role['id']})

    name = gen_alpha()
    content = gen_alpha()

    report_template = module_target_sat.cli.ReportTemplate.with_user(
        username=user1['login'], password=password
    ).create(
        {'name': name, 'organization-id': org['id'], 'location-id': loc['id'], 'file': content}
    )

    schedule = module_target_sat.cli.ReportTemplate.with_user(
        username=user1['login'], password=password
    ).schedule({'name': report_template['name']})
    job_id = schedule.split('Job ID: ', 1)[1].strip()

    report_data = module_target_sat.cli.ReportTemplate.with_user(
        username=user1['login'], password=password
    ).report_data({'id': report_template['name'], 'job-id': job_id})

    assert content in report_data
    with pytest.raises(CLIReturnCodeError):
        module_target_sat.cli.ReportTemplate.with_user(
            username=user2['login'], password=password
        ).report_data({'id': report_template['name'], 'job-id': job_id})


def test_positive_generate_with_name_and_org(module_target_sat):
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

    :customerscenario: true

    :BZ: 1750924
    """
    host_name = gen_alpha()
    host = module_target_sat.cli_factory.make_fake_host({'name': host_name})

    result = module_target_sat.cli.ReportTemplate.generate(
        {'name': 'Host - Statuses', 'organization': DEFAULT_ORG}
    )
    assert 'RHEL lifecycle' in result
    assert host['name'] in [item.split(',')[0] for item in result.split('\n')]


def test_positive_generate_ansible_template(module_target_sat):
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
    settings = module_target_sat.cli.Settings.list({'search': 'name=ansible_inventory_template'})
    assert len(settings) == 1
    template_name = settings[0]['value']

    report_list = module_target_sat.cli.ReportTemplate.list()
    assert template_name in [rt['name'] for rt in report_list]

    login = gen_alpha().lower()
    password = gen_alpha().lower()
    loc = module_target_sat.cli.Location.info({'name': DEFAULT_LOC})
    org = module_target_sat.cli.Org.info({'name': DEFAULT_ORG})

    user = module_target_sat.cli_factory.user(
        {
            'login': login,
            'password': password,
            'organization-ids': org['id'],
            'location-ids': loc['id'],
        }
    )

    module_target_sat.cli.User.add_role(
        {'login': user['login'], 'role': 'Ansible Tower Inventory Reader'}
    )

    host_name = gen_alpha().lower()
    host = module_target_sat.cli_factory.make_fake_host({'name': host_name})

    schedule = module_target_sat.cli.ReportTemplate.with_user(
        username=user['login'], password=password
    ).schedule({'name': template_name, 'inputs': 'Content Attributes=yes'})

    job_id = schedule.split('Job ID: ', 1)[1].strip()
    report_data = module_target_sat.cli.ReportTemplate.with_user(
        username=user['login'], password=password
    ).report_data({'name': template_name, 'job-id': job_id})

    assert host['name'] in [item.split(',')[1] for item in report_data.split('\n') if len(item) > 0]


def test_positive_generate_hostpkgcompare(
    module_sca_manifest_org, local_ak, local_content_view, local_environment, target_sat
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
    target_sat.cli_factory.setup_org_for_a_rh_repo(
        {
            'product': PRDS['rhel'],
            'repository-set': REPOSET['rhst7'],
            'repository': REPOS['rhst7']['name'],
            'organization-id': module_sca_manifest_org.id,
            'content-view-id': local_content_view['id'],
            'lifecycle-environment-id': local_environment['id'],
            'activationkey-id': local_ak['id'],
        },
        force=True,
    )
    target_sat.cli_factory.setup_org_for_a_custom_repo(
        {
            'url': settings.repos.yum_6.url,
            'organization-id': module_sca_manifest_org.id,
            'content-view-id': local_content_view['id'],
            'lifecycle-environment-id': local_environment['id'],
            'activationkey-id': local_ak['id'],
        }
    )

    clients = []
    with Broker(nick='rhel7', host_class=ContentHost, _count=2) as hosts:
        for client in hosts:
            # Create RHEL hosts via broker and register content host
            result = client.register(
                module_sca_manifest_org,
                None,
                local_ak.name,
                target_sat,
            )
            assert result.status == 0, f'Failed to register host: {result.stderr}'
            assert client.subscribed
            clients.append(client)
            client.enable_repo(REPOS['rhst7']['id'])
        clients.sort(key=lambda client: client.hostname)
        hosts_info = [target_sat.cli.Host.info({'name': client.hostname}) for client in clients]

        host1, host2 = hosts_info
        res = clients[0].execute(
            f'yum -y install {FAKE_0_CUSTOM_PACKAGE_NAME} {FAKE_1_CUSTOM_PACKAGE}'
        )
        assert not res.status
        res = clients[1].execute(f'yum -y install {FAKE_2_CUSTOM_PACKAGE}')
        assert not res.status

        result = target_sat.cli.ReportTemplate.generate(
            {
                'name': 'Host - compare content hosts packages',
                'inputs': f'Host 1 = {host1["name"]}, Host 2 = {host2["name"]}',
            }
        )

        result = result.split('\n')
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


def test_negative_generate_hostpkgcompare_nonexistent_host(module_target_sat):
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
        module_target_sat.cli.ReportTemplate.generate(
            {
                'name': 'Host - compare content hosts packages',
                'inputs': 'Host 1 = nonexistent1, Host 2 = nonexistent2',
            }
        )
    assert "At least one of the hosts couldn't be found" in cm.value.stderr


@pytest.mark.rhel_ver_match('N-2')
def test_positive_generate_installed_packages_report(
    module_sca_manifest_org,
    rhel_contenthost,
    local_content_view,
    local_environment,
    local_ak,
    target_sat,
):
    """Generate an report using the 'Host - All Installed Packages' Report template

    :id: 47cc5528-41d9-4100-b603-e98d2ff097a8

    :setup: Installed Satellite with Organization, Activation key,
            Content View, Content Host, and custom product containing packages

    :steps:
        1. hammer report-template generate --name 'Host - All Installed Packages'
            --organization-title '' --report-format '' --inputs 'Hosts filter = hostname'

    :expectedresults: A report is generated containing all installed package
            information for a host

    :BZ: 1826648

    :parametrized: yes

    :customerscenario: true
    """
    target_sat.cli_factory.setup_org_for_a_custom_repo(
        {
            'url': settings.repos.yum_6.url,
            'organization-id': module_sca_manifest_org.id,
            'content-view-id': local_content_view['id'],
            'lifecycle-environment-id': local_environment['id'],
            'activationkey-id': local_ak['id'],
        }
    )
    client = rhel_contenthost
    result = client.register(
        module_sca_manifest_org,
        None,
        local_ak.name,
        target_sat,
    )
    assert result.status == 0, f'Failed to register host: {result.stderr}'
    assert client.subscribed
    client.execute(f'yum -y install {FAKE_0_CUSTOM_PACKAGE_NAME} {FAKE_1_CUSTOM_PACKAGE}')
    result_html = target_sat.cli.ReportTemplate.generate(
        {
            'organization': module_sca_manifest_org.name,
            'name': 'Host - All Installed Packages',
            'report-format': 'html',
            'inputs': f'Hosts filter={client.hostname}',
        }
    )
    assert client.hostname in result_html
    assert FAKE_1_CUSTOM_PACKAGE in result_html


@pytest.mark.rhel_ver_list([settings.content_host.default_rhel_version])
def test_positive_generate_with_no_rex_interface(
    module_org,
    rex_contenthost,
    target_sat,
):
    """Generate an report using the 'Ansible - Ansible Inventory' report template

    :id: ee77f0d8-0279-4707-8f36-c7ca51f8c373

    :steps:
        1. Disable remote execution on the host interface
        2. Generate report

    :expectedresults: report successfully generated

    :Verifies: SAT-33189

    :customerscenario: true
    """
    host = target_sat.cli.Host.info({'name': rex_contenthost.hostname})
    for host_interface in host['network-interfaces'].values():
        result = target_sat.cli.HostInterface.update(
            {
                'host-id': host['id'],
                'id': host_interface['id'],
                'execution': 'false',
            }
        )
        assert 'interface updated' in result[0]['message'].lower()
    result_html = target_sat.cli.ReportTemplate.generate(
        {
            'organization': module_org.name,
            'name': 'Ansible - Ansible Inventory',
            'report-format': 'html',
        }
    )
    assert rex_contenthost.hostname in result_html
