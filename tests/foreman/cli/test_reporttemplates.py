# -*- encoding: utf-8 -*-
"""
:Requirement: Report templates

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: Reporting

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_string

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
from robottelo.cli.filter import Filter
from robottelo.cli.location import Location
from robottelo.cli.org import Org
from robottelo.cli.report_template import ReportTemplate
from robottelo.cli.repository import Repository
from robottelo.cli.settings import Settings
from robottelo.cli.subscription import Subscription
from robottelo.cli.user import User
from robottelo.constants import DEFAULT_LOC
from robottelo.constants import DEFAULT_ORG
from robottelo.constants import DISTRO_RHEL7
from robottelo.constants import REPORT_TEMPLATE_FILE
from robottelo.decorators import stubbed
from robottelo.decorators import tier1
from robottelo.decorators import tier2
from robottelo.decorators import tier3
from robottelo.ssh import upload_file
from robottelo.test import CLITestCase
from robottelo.vm import VirtualMachine


@pytest.fixture(scope='class')
def setup_content(request):
    """Pytest fixture for setting up an organization, manifest, content-view,
    lifecycle environment, and activation key with subscriptions"""
    org = make_org()
    with manifests.clone() as manifest:
        upload_file(manifest.content, manifest.filename)
    new_product = make_product({u'organization-id': org['id']})
    new_repo = make_repository({u'product-id': new_product['id']})
    Repository.synchronize({'id': new_repo['id']})
    content_view = make_content_view({'organization-id': org['id']})
    ContentView.add_repository(
        {
            u'id': content_view['id'],
            u'organization-id': org['id'],
            u'repository-id': new_repo['id'],
        }
    )
    ContentView.publish({'id': content_view['id']})
    env = make_lifecycle_environment({'organization-id': org['id']})
    cvv = ContentView.info({'id': content_view['id']})['versions'][0]
    ContentView.version_promote({'id': cvv['id'], 'to-lifecycle-environment-id': env['id']})
    new_ak = make_activation_key(
        {
            'lifecycle-environment-id': env['id'],
            'content-view': content_view['name'],
            'organization-id': org['id'],
            'auto-attach': False,
        }
    )
    subs_id = Subscription.list({'organization-id': org['id']}, per_page=False)
    ActivationKey.add_subscription({'id': new_ak['id'], 'subscription-id': subs_id[0]['id']})
    request.cls.setup_org = org
    request.cls.setup_new_ak = new_ak
    request.cls.setup_subs_id = subs_id


@pytest.mark.usefixtures("setup_content")
class ReportTemplateTestCase(CLITestCase):
    """Report Templates CLI tests."""

    @tier2
    def test_positive_report_help(self):
        """ hammer level of help included in test:
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

        :CaseImportance: High
        """
        base = Base().execute('--help')
        self.assertGreater(len([i for i in base if 'report-template' in i]), 0)
        base = Base().execute('report-template --help')
        self.assertGreater(len([i for i in base if 'hammer report-template' in i]), 0)
        self.assertGreater(len([i for i in base if 'info' and 'report template' in i]), 0)
        self.assertGreater(len([i for i in base if 'generate' and 'report' in i]), 0)
        base = Base().execute('report-template create --help')
        self.assertGreater(len([i for i in base if 'hammer report-template create' in i]), 0)
        self.assertGreater(len([i for i in base if '--audit-comment' in i]), 0)
        self.assertGreater(len([i for i in base if '--interactive' in i]), 0)

    @tier1
    def test_positive_end_to_end_crud_and_list(self):
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
        name = gen_string('alpha')
        report_template = make_report_template({'name': name})
        self.assertEqual(report_template['name'], name)

        # list - create second template
        tmp_name = gen_string('alpha')
        tmp_report_template = make_report_template({'name': tmp_name})
        result_list = ReportTemplate.list()
        self.assertIn(name, [rt['name'] for rt in result_list])

        # info
        result = ReportTemplate.info({'id': report_template['id']})
        self.assertEqual(result['name'], name)

        # update
        new_name = gen_string('alpha')
        result = ReportTemplate.update({'name': report_template['name'], 'new-name': new_name})
        self.assertEqual(result[0]['name'], new_name)
        rt_list = ReportTemplate.list()
        self.assertNotIn(name, [rt['name'] for rt in rt_list])

        # delete tmp
        ReportTemplate.delete({'name': tmp_report_template['name']})
        with self.assertRaises(CLIReturnCodeError):
            ReportTemplate.info({u'id': tmp_report_template['id']})

    @tier1
    def test_positive_generate_report_nofilter_and_with_filter(self):
        """Generate Host Status report without filter and with filter

        :id: 5af03399-b918-468a-9306-1c76dda6a369

        :setup: User with reporting access rights, some report template, at least two hosts

        :steps:

            0. use default report template called Host statuses
            1. hammer report-template generate --id ... # do not specify any filter
            2. hammer report-template generate --id ... # specify filter

        :expectedresults: nofilter - Report is generated for all hosts visible for user
                          filter   - Report is generated for the host specified by the filter

        :CaseImportance: Critical
        """
        host_name = gen_string('alpha')
        host1 = make_fake_host({'name': host_name})

        host_name_2 = gen_string('alpha')
        host2 = make_fake_host({'name': host_name_2})

        result_list = ReportTemplate.list()
        self.assertIn('Host statuses', [rt['name'] for rt in result_list])

        rt_host_statuses = ReportTemplate.info({'name': 'Host statuses'})
        result_no_filter = ReportTemplate.generate({'name': rt_host_statuses['name']})

        self.assertIn(host1['name'], [item.split(',')[0] for item in result_no_filter])
        self.assertIn(host2['name'], [item.split(',')[0] for item in result_no_filter])

        result = ReportTemplate.generate(
            {
                'name': rt_host_statuses['name'],
                'inputs': (
                    rt_host_statuses['template-inputs'][0]['name']
                    + "="
                    + 'name={0}'.format(host1['name'])
                ),
            }
        )
        self.assertIn(host1['name'], [item.split(',')[0] for item in result])
        self.assertNotIn(host2['name'], [item.split(',')[0] for item in result])

    @tier2
    def test_positive_lock_and_unlock_report(self):
        """Lock and unlock report template

        :id: df306515-8798-4ce3-9430-6bc3bf9b9b33

        :setup: User with reporting access rights, some report template that is not locked

        :steps:

            1. hammer report-template update ... --locked true
            2. hammer report-template update ... --locked false

        :expectedresults: Report is locked and unlocked successfully.

        :CaseImportance: Medium
        """
        name = gen_string('alpha')
        report_template = make_report_template({'name': name})
        ReportTemplate.update({'name': report_template['name'], 'locked': 1})
        new_name = gen_string('alpha')
        with self.assertRaises(CLIReturnCodeError):
            ReportTemplate.update({'name': report_template['name'], 'new-name': new_name})

        ReportTemplate.update({'name': report_template['name'], 'locked': 0})
        result = ReportTemplate.update({'name': report_template['name'], 'new-name': new_name})
        self.assertEqual(result[0]['name'], new_name)

    @tier2
    def test_positive_report_add_userinput(self):
        """Add user input to template

        :id: 84b577db-144e-4761-a46e-e83887464986

        :setup: User with reporting access rights

        :steps:

            1. hammer template-input create ...

        :expectedresults: User input is assigned to the report template

        :CaseImportance: High
        """
        name = gen_string('alpha')
        report_template = make_report_template({'name': name})
        ti_name = gen_string('alpha')
        template_input = make_template_input(
            {'name': ti_name, 'input-type': 'user', 'template-id': report_template['id']}
        )
        result = ReportTemplate.info({'name': report_template['name']})
        self.assertEqual(result['template-inputs'][0]['name'], template_input['name'])

    @tier2
    def test_positive_dump_report(self):
        """Export report template

        :id: 84b577db-144e-4761-a42e-a83887464986

        :setup: User with reporting access rights, some report template

        :steps:

            1. hammer report-template dump ...

        :expectedresults: Report script is shown

        :CaseImportance: Medium
        """
        name = gen_string('alpha')
        content = gen_string('alpha')
        report_template = make_report_template({'name': name, 'content': content})
        result = ReportTemplate.dump({'id': report_template['id']})
        self.assertIn(content, result)

    @tier2
    def test_positive_clone_locked_report(self):
        """Clone locked report template

        :id: cc843731-b9c2-4fc9-9e15-d1ee5d967cda

        :setup: User with reporting access rights, some report template that is locked

        :steps:

            1. hammer report-template clone ...

        :expectedresults: Report is cloned

        :CaseImportance: Medium
        """

        name = gen_string('alpha')
        report_template = make_report_template({'name': name})
        ReportTemplate.update({'name': report_template['name'], 'locked': 1, 'default': 1})
        new_name = gen_string('alpha')
        ReportTemplate.clone({'id': report_template['id'], 'new-name': new_name})
        result_list = ReportTemplate.list()
        self.assertIn(new_name, [rt['name'] for rt in result_list])
        result_info = ReportTemplate.info({'id': report_template['id']})
        self.assertEqual(result_info['locked'], 'yes')
        self.assertEqual(result_info['default'], 'yes')

    @tier2
    def test_positive_generate_report_sanitized(self):
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
        os_name = gen_string('alpha') + "," + gen_string('alpha')
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

        host_name = gen_string('alpha')
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
        self.assertIn('Name,Operating System', result)  # verify header of custom template
        self.assertIn(
            '{0},"{1}"'.format(host['name'], host['operating-system']['operating-system']), result
        )

    @tier3
    @stubbed()
    def test_positive_applied_errata(self):
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

        :CaseImportance: High
        """

    @tier2
    @stubbed()
    def test_positive_generate_email_compressed(self):
        """Generate an Applied Errata report, get it by e-mail, compressed

        :id: a4b877db-143e-4871-a42e-e93887464986

        :setup: User with reporting access rights, some host with applied errata

        :steps:

            1. hammer report-template schedule ...

        :expectedresults: A report is generated asynchronously, the result
                          is compressed and mailed to the specified address

        :CaseImportance: Medium
        """

    @tier2
    @stubbed()
    def test_positive_generate_email_uncompressed(self):
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

    @tier2
    def test_negative_create_report_without_name(self):
        """Try to create a report template with empty name

        :id: 84b577db-144e-4771-a42e-e93887464986

        :setup: User with reporting access rights

        :steps:

            1. hammer report-template create --name '' ...

        :expectedresults: Report is not created

        :CaseImportance: Medium
        """
        with self.assertRaises(CLIFactoryError):
            make_report_template({'name': ''})

    @tier2
    def test_negative_delete_locked_report(self):
        """Try to delete a locked report template

        :id: 84b577db-144e-4871-a42e-e93887464986

        :setup: User with reporting access rights, some report template that is locked

        :steps:

            1. hammer report-template delete ...

        :expectedresults: Report is not deleted

        :CaseImportance: Medium
        """
        name = gen_string('alpha')
        report_template = make_report_template({'name': name})

        ReportTemplate.update({'name': report_template['name'], 'locked': 1})

        with self.assertRaises(CLIReturnCodeError):
            ReportTemplate.delete({'name': report_template['name']})

    @tier2
    def test_negative_bad_email(self):
        """ Report can't be generated when incorrectly formed mail specified

        :id: a4ba77db-144e-4871-a42e-e93887464986

        :setup: User with reporting access rights, some host with applied errata

        :steps:

            1. hammer report-template schedule ...

        :expectedresults: Error message about wrong e-mail address, no task is triggered

        :CaseImportance: Medium
        """
        name = gen_string('alpha')
        report_template = make_report_template({'name': name})

        with self.assertRaises(CLIReturnCodeError):
            ReportTemplate.schedule(
                {'name': report_template['name'], 'mail-to': gen_string('alpha')}
            )

    @tier3
    def test_negative_nonauthor_of_report_cant_download_it(self):
        """The resulting report should only be downloadable by
           the user that generated it or admin. Check.

        :id: a4bc77db-146e-4871-a42e-e93887464986

        :setup: Installed Satellite, user that can list running tasks

        :steps:

            1. hammer -u u1 -p p1 report-template schedule
            2. hammer -u u2 -p p2 report-template report-data

        :expectedresults: Report can't be downloaded. Error.

        :CaseImportance: High
        """
        uname_viewer = gen_string('alpha')
        uname_viewer2 = gen_string('alpha')
        password = gen_string('alpha')

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
            for permission in Filter.available_permissions({'resource-type': 'Organization'})
        ]
        permissions_loc = [
            permission['name']
            for permission in Filter.available_permissions({'resource-type': 'Location'})
        ]
        permissions_rt = [
            permission['name']
            for permission in Filter.available_permissions({'resource-type': 'ReportTemplate'})
        ]
        permissions_pt = [
            permission['name']
            for permission in Filter.available_permissions(
                {'resource-type': 'ProvisioningTemplate'}
            )
        ]
        permissions_jt = [
            permission['name']
            for permission in Filter.available_permissions({'resource-type': 'JobTemplate'})
        ]
        # Assign filters to created role
        make_filter({'role-id': role['id'], 'permissions': permissions_org})
        make_filter({'role-id': role['id'], 'permissions': permissions_loc})
        make_filter({'role-id': role['id'], 'permissions': permissions_rt})
        make_filter({'role-id': role['id'], 'permissions': permissions_pt})
        make_filter({'role-id': role['id'], 'permissions': permissions_jt})
        User.add_role({'login': user1['login'], 'role-id': role['id']})
        User.add_role({'login': user2['login'], 'role-id': role['id']})

        name = gen_string('alpha')
        content = gen_string('alpha')

        report_template = ReportTemplate.with_user(
            username=user1['login'], password=password
        ).create(
            {'name': name, 'organization-id': org['id'], 'location-id': loc['id'], 'file': content}
        )

        schedule = ReportTemplate.with_user(username=user1['login'], password=password).schedule(
            {'name': report_template['name']}
        )

        report_data = ReportTemplate.with_user(
            username=user1['login'], password=password
        ).report_data(
            {'id': report_template['name'], 'job-id': schedule[0].split("Job ID: ", 1)[1]}
        )

        self.assertIn(content, report_data)
        with self.assertRaises(CLIReturnCodeError):
            ReportTemplate.with_user(username=user2['login'], password=password).report_data(
                {'id': report_template['name'], 'job-id': schedule[0].split("Job ID: ", 1)[1]}
            )

    @tier2
    @pytest.mark.skip_if_open('BZ:1750924')
    def test_positive_generate_with_name_and_org(self):
        """Generate Host Status report, specifying template name and organization

        :id: 5af03399-b918-468a-1306-1c76dda6f369

        :setup: User with reporting access rights, some report template, some host

        :steps:

            0. use default report template called Host statuses
            1. hammer report-template generate --name ... --organization ...

        :expectedresults: Report successfully generated (in BZ, it results in
            "ERF42-5227 [Foreman::Exception]: unknown parent permission for
            api/v2/report_templates#generate")

        :CaseImportance: Medium

        :BZ: 1750924
        """
        host_name = gen_string('alpha')
        host = make_fake_host({'name': host_name})

        result = ReportTemplate.generate({'name': 'Host statuses', 'organization': DEFAULT_ORG})

        self.assertIn(host['name'], [item.split(',')[0] for item in result])

    @tier2
    @pytest.mark.skip_if_open('BZ:1782807')
    def test_positive_generate_ansible_template(self):
        """ Report template named 'Ansible Inventory' (default name is specified in settings)
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

        login = gen_string('alpha').lower()
        password = gen_string('alpha').lower()
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

        host_name = gen_string('alpha').lower()
        host = make_fake_host({'name': host_name})

        schedule = ReportTemplate.with_user(username=user['login'], password=password).schedule(
            {'name': template_name}
        )

        report_data = ReportTemplate.with_user(
            username=user['login'], password=password
        ).report_data({'id': template_name, 'job-id': schedule[0].split("Job ID: ", 1)[1]})

        assert host['name'] in [item.split(',')[1] for item in report_data if len(item) > 0]

    @tier3
    def test_positive_generate_entitlements_report_multiple_formats(self):
        """Generate an report using the Entitlements template in html, yaml, and csv format.

        :id: f2b74916-1298-4d20-9c24-a2c2b3a3e9a9

        :setup: Installed Satellite with Organization, Activation key,
                Content View, Content Host, and Subscriptions.

        :steps:
            1. hammer report-template generate --organization '' --id '' --report-format ''

        :expectedresults: report is generated containing all the expected information
                          regarding Entitlements.

        :CaseImportance: High
        """
        with VirtualMachine(distro=DISTRO_RHEL7) as vm:
            vm.install_katello_ca()
            vm.register_contenthost(self.setup_org['label'], self.setup_new_ak['name'])
            assert vm.subscribed
            result_html = ReportTemplate.generate(
                {'organization': self.setup_org['name'], 'id': 115, 'report-format': 'html'}
            )
            assert vm.hostname in result_html[2]
            assert self.setup_subs_id[0]['name'] in result_html[2]
            result_yaml = ReportTemplate.generate(
                {'organization': self.setup_org['name'], 'id': 115, 'report-format': 'yaml'}
            )
            for entry in result_yaml:
                if '-Name:' in entry:
                    assert vm.hostname in entry
                elif 'Subscription Name:' in entry:
                    assert self.setup_subs_id[0]['name'] in entry
            result_csv = ReportTemplate.generate(
                {'organization': self.setup_org['name'], 'id': 115, 'report-format': 'csv'}
            )
            assert vm.hostname in result_csv[1]
            assert self.setup_subs_id[0]['name'] in result_csv[1]

    @tier3
    def test_positive_schedule_Entitlements_report(self):
        """Schedule an report using the Entitlements template in csv format.

        :id: 572fb387-86e0-40e2-b2df-e8ec26433610


        :setup: Installed Satellite with Organization, Activation key,
                Content View, Content Host, and Subscriptions.

        :steps:
            1. hammer report-template schedule --organization '' --id '' --report-format ''

        :expectedresults: report is scheduled and generated containing all the expected information
                          regarding Entitlements.

        :CaseImportance: High
        """
        with VirtualMachine(distro=DISTRO_RHEL7) as vm:
            vm.install_katello_ca()
            vm.register_contenthost(self.setup_org['label'], self.setup_new_ak['name'])
            assert vm.subscribed
            scheduled_csv = ReportTemplate.schedule(
                {'id': 115, 'organization': self.setup_org['name'], 'report-format': 'csv'}
            )
            data_csv = ReportTemplate.report_data(
                {'id': 115, 'job-id': scheduled_csv[0].split("Job ID: ", 1)[1]}
            )
            for item in data_csv:
                if vm.hostname == item:
                    assert vm.hostname in data_csv
            for item in data_csv:
                if self.setup_subs_id[0]['name'] == item:
                    assert self.setup_subs_id[0]['name'] in data_csv
