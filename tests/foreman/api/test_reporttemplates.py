# -*- encoding: utf-8 -*-
"""Unit tests for the ``report_templates`` paths.

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
from nailgun import entities
from requests import HTTPError

from robottelo import manifests
from robottelo.api.utils import enable_rhrepo_and_fetchid
from robottelo.api.utils import promote
from robottelo.api.utils import upload_manifest
from robottelo.constants import DEFAULT_SUBSCRIPTION_NAME
from robottelo.constants import DISTRO_RHEL7
from robottelo.constants import PRDS
from robottelo.constants import REPOS
from robottelo.constants import REPOSET
from robottelo.datafactory import valid_data_list
from robottelo.decorators import tier1
from robottelo.decorators import tier2
from robottelo.decorators import tier3
from robottelo.test import APITestCase
from robottelo.utils.issue_handlers import is_open
from robottelo.vm import VirtualMachine


@pytest.fixture(scope='class')
def setup_content(request):
    org = entities.Organization().create()
    with manifests.clone() as manifest:
        upload_manifest(org.id, manifest.content)
    rh_repo_id = enable_rhrepo_and_fetchid(
        basearch='x86_64',
        org_id=org.id,
        product=PRDS['rhel'],
        repo=REPOS['rhst7']['name'],
        reposet=REPOSET['rhst7'],
        releasever=None,
    )
    rh_repo = entities.Repository(id=rh_repo_id).read()
    rh_repo.sync()
    custom_repo = entities.Repository(
        product=entities.Product(organization=org).create(),
    ).create()
    custom_repo.sync()
    lce = entities.LifecycleEnvironment(organization=org).create()
    cv = entities.ContentView(organization=org, repository=[rh_repo_id, custom_repo.id],).create()
    cv.publish()
    cvv = cv.read().version[0].read()
    promote(cvv, lce.id)
    ak = entities.ActivationKey(
        content_view=cv, max_hosts=100, organization=org, environment=lce, auto_attach=True
    ).create()
    subscription = entities.Subscription(organization=org).search(
        query={'search': 'name="{}"'.format(DEFAULT_SUBSCRIPTION_NAME)}
    )[0]
    ak.add_subscriptions(data={'quantity': 1, 'subscription_id': subscription.id})
    request.cls.org_setup = org
    request.cls.ak_setup = ak


class ReportTemplateTestCase(APITestCase):
    """Tests for ``katello/api/v2/report_templates``."""

    @tier1
    def test_positive_CRUDL(self):
        """Create, Read, Update, Delete, List

        :id: a2a577db-144e-4761-a42e-e83885464786

        :setup: User with reporting access rights

        :steps:

            1. Create Report Template
            2. List Report Templates, verify it's there
            3. Read Report Template
            4. Update Report Template, read again
            5. Delete Report template, check it's not present

        :expectedresults: All operations succeed, no template present in the end

        :CaseImportance: Critical
        """
        # Create
        rt = None
        name = None
        template1 = gen_string('alpha')
        for name in valid_data_list():
            rt = entities.ReportTemplate(name=name, template=template1).create()
        # List
        res = entities.ReportTemplate().search(query={'search': 'name="{}"'.format(name)})
        assert name in list(map(lambda x: x.name, res))
        # Read
        rt = entities.ReportTemplate(id=rt.id).read()
        assert name == rt.name
        assert template1 == rt.template
        # Update
        template2 = gen_string('alpha')
        entities.ReportTemplate(id=rt.id, template=template2).update(['template'])
        rt = entities.ReportTemplate(id=rt.id).read()
        assert template2 == rt.template
        # Delete
        entities.ReportTemplate(id=rt.id).delete()
        with pytest.raises(HTTPError):
            rt = entities.ReportTemplate(id=rt.id).read()

    @tier1
    def test_positive_generate_report_nofilter(self):
        """Generate Host - Statuses report

        :id: a4b687db-144e-4761-a42e-e93887464986

        :setup: User with reporting access rights, some report template, at least two hosts

        :steps:

            1. POST /api/report_templates/:id/generate

        :expectedresults: Report is generated for all hosts visible to user

        :CaseImportance: Critical
        """
        host_name = gen_string('alpha').lower()
        entities.Host(name=host_name).create()
        rt = entities.ReportTemplate().search(query={'search': 'name="Host - Statuses"'})[0].read()
        res = rt.generate()
        assert "Service Level" in res
        assert host_name in res

    @tier2
    def test_positive_generate_report_filter(self):
        """Generate Host - Statuses report

        :id: a4b677cb-144e-4761-a42e-e93887464986

        :setup: User with reporting access rights, some report template, at least two hosts

        :steps:

            1. POST /api/report_templates/:id/generate ... # define input_values

        :expectedresults: Report is generated (only) for the host specified by the filter

        :CaseImportance: High
        """
        host1_name = gen_string('alpha').lower()
        host2_name = gen_string('alpha').lower()
        entities.Host(name=host1_name).create()
        entities.Host(name=host2_name).create()
        rt = entities.ReportTemplate().search(query={'search': 'name="Host - Statuses"'})[0].read()
        res = rt.generate(data={"input_values": {"hosts": host2_name}})
        assert "Service Level" in res
        assert host1_name not in res
        assert host2_name in res

    @tier2
    def test_positive_report_add_userinput(self):
        """Add user input to template, use it in template, generate template

        :id: a4a577db-144e-4761-a42e-e86887464986

        :setup: User with reporting access rights

        :steps:

            1. PUT /api/templates/:template_id/template_inputs/:id ... # add user input

        :expectedresults: User input is assigned to the report template and used in template

        :CaseImportance: High
        """
        host_name = gen_string('alpha').lower()
        input_name = gen_string('alpha').lower()
        input_value = gen_string('alpha').lower()
        template_name = gen_string('alpha').lower()
        template = '<%= "value=\\"" %><%= input(\'{0}\') %><%= "\\"" %>'.format(input_name)
        entities.Host(name=host_name).create()
        rt = entities.ReportTemplate(name=template_name, template=template).create()
        entities.TemplateInput(name=input_name, input_type="user", template=rt.id,).create()
        ti = entities.TemplateInput(template=rt.id).search()[0].read()
        assert input_name == ti.name
        res = rt.generate(data={"input_values": {input_name: input_value}})
        assert 'value="{}"'.format(input_value) in res

    @tier2
    def test_positive_lock_clone_nodelete_unlock_report(self):
        """Lock report template. Check it can be cloned and can't be deleted or edited.
           Unlock. Check it can be deleted and edited.

        :id: a4c577db-144e-4761-a42e-e83887464986

        :setup: User with reporting access rights, some report template that is not locked

        :steps:

            1. Create template
            2. Lock template
            3. Clone template, check cloned data
            4. Try to delete template
            5. Try to edit template
            6. Unlock template
            7. Edit template
            8. Delete template

        :expectedresults: Report is locked

        :CaseImportance: High

        :BZ: 1680458
        """
        # 1. Create template
        template_name = gen_string('alpha').lower()
        template_clone_name = gen_string('alpha').lower()
        template1 = gen_string('alpha')
        template2 = gen_string('alpha')
        rt = entities.ReportTemplate(name=template_name, template=template1).create()
        # 2. Lock template
        entities.ReportTemplate(id=rt.id, locked=True).update(["locked"])
        rt = rt.read()
        assert rt.locked is True
        # 3. Clone template, check cloned data
        rt.clone(data={'name': template_clone_name})
        cloned_rt = (
            entities.ReportTemplate()
            .search(query={'search': 'name="{}"'.format(template_clone_name)})[0]
            .read()
        )
        assert template_clone_name == cloned_rt.name
        assert template1 == cloned_rt.template
        # 4. Try to delete template
        if not is_open('BZ:1680458'):
            with pytest.raises(HTTPError):
                rt.delete()
            # In BZ1680458, exception is thrown but template is deleted anyway
            assert (
                len(
                    entities.ReportTemplate().search(
                        query={'search': 'name="{}"'.format((template_name))}
                    )
                )
                != 0
            )
        # 5. Try to edit template
        with self.assertRaises(HTTPError):
            entities.ReportTemplate(id=rt.id, template=template2).update(["template"])
        rt = rt.read()
        assert template1 == rt.template
        # 6. Unlock template
        entities.ReportTemplate(id=rt.id, locked=False).update(["locked"])
        rt = rt.read()
        assert rt.locked is False
        # 7. Edit template
        entities.ReportTemplate(id=rt.id, template=template2).update(["template"])
        rt = rt.read()
        assert template2 == rt.template
        # 8. Delete template
        rt.delete()
        assert (
            len(
                entities.ReportTemplate().search(
                    query={'search': 'name="{}"'.format((template_name))}
                )
            )
            == 0
        )

    @tier2
    @pytest.mark.stubbed
    def test_positive_export_report(self):
        """Export report template

        :id: a4b577db-144e-4761-a42e-a83887464986

        :setup: User with reporting access rights, some report template

        :steps:

            1. /api/report_templates/:id/export

        :expectedresults: Report script is shown

        :CaseImportance: High
        """

    @tier2
    @pytest.mark.stubbed
    def test_positive_generate_report_sanitized(self):
        """Generate report template where there are values in comma outputted which might brake CSV format

        :id: a4b577db-144e-4961-a42e-e93887464986

        :setup: User with reporting access rights, Host Statuses report,
                a host with OS that has comma in its name

        :steps:

            1. POST /api/report_templates/:id/generate

        :expectedresults: Report is generated in proper CSV format (value with comma is quoted)

        :CaseImportance: Medium
        """

    @tier2
    @pytest.mark.stubbed
    def test_negative_create_report_without_name(self):
        """Try to create a report template with empty name

        :id: a4b577db-144e-4771-a42e-e93887464986

        :setup: User with reporting access rights

        :steps:

            1. POST /api/report_templates

        :expectedresults: Report is not created

        :CaseImportance: Medium
        """

    @tier2
    @pytest.mark.stubbed
    def test_positive_applied_errata(self):
        """Generate an Applied Errata report

        :id: a4b577db-141e-4871-a42e-e93887464986

        :setup: User with reporting access rights, some host with applied errata

        :steps:

            1. POST /api/report_templates/:id/generate

        :expectedresults: A report is generated with all applied errata listed

        :CaseImportance: Medium
        """

    @tier2
    @pytest.mark.stubbed
    def test_positive_generate_nonblocking(self):
        """Generate an Applied Errata report

        :id: a4b577db-142e-4871-a42e-e93887464986

        :setup: User with reporting access rights, some host with applied errata

        :steps:

            1. POST /api/report_templates/:id/schedule_report
            2. GET /api/report_templates/:id/report_data/:job_id

        :expectedresults: A report is generated asynchronously

        :CaseImportance: Medium
        """

    @tier2
    @pytest.mark.stubbed
    def test_positive_generate_email_compressed(self):
        """Generate an Applied Errata report, get it by e-mail, compressed

        :id: a4b577db-143e-4871-a42e-e93887464986

        :setup: User with reporting access rights, some host with applied errata

        :steps:

            1. POST /api/report_templates/:id/schedule_report

        :expectedresults: A report is generated asynchronously, the result
                          is compressed and mailed to the specified address

        :CaseImportance: Medium
        """

    @tier2
    @pytest.mark.stubbed
    def test_positive_generate_email_uncompressed(self):
        """Generate an Applied Errata report, get it by e-mail, uncompressed

        :id: a4b577db-143f-4871-a42e-e93887464986

        :setup: User with reporting access rights, some host with applied errata

        :steps:

            1. POST /api/report_templates/:id/schedule_report

        :expectedresults: A report is generated asynchronously, the result
                          is not compressed and is mailed
                          to the specified address

        :CaseImportance: Medium
        """

    @tier2
    @pytest.mark.stubbed
    def test_negative_bad_email(self):
        """ Report can't be generated when incorrectly formed mail specified

        :id: a4b577db-164e-4871-a42e-e93887464986

        :setup: User with reporting access rights, some host with applied errata

        :steps:

            1. POST /api/report_templates/:id/schedule_report

        :expectedresults: Error message about wrong e-mail address, no task is triggered

        :CaseImportance: Medium
        """

    @tier2
    @pytest.mark.stubbed
    def test_positive_cleanup_task_running(self):
        """ Report can't be generated when incorrectly formed mail specified

        :id: a4b577db-145e-4871-a42e-e93887464986

        :setup: Installed Satellite, user that can list running tasks

        :steps:

            1. List running tasks

        :expectedresults: Report cleanup task is running

        :CaseImportance: Medium
        """

    @tier2
    @pytest.mark.stubbed
    def test_negative_nonauthor_of_report_cant_download_it(self):
        """The resulting report should only be downloadable by
           the user that generated it or admin. Check.

        :id: a4b577db-146e-4871-a42e-e93887464986

        :setup: Installed Satellite, user that can list running tasks

        :steps:

            1. POST /api/report_templates/:id/schedule_report
            2. GET /api/report_templates/:id/report_data/:job_id (as a different non-admin user)

        :expectedresults: Report can't be downloaded. Error.

        :CaseImportance: Medium
        """

    @tier3
    @pytest.mark.usefixtures("setup_content")
    def test_positive_generate_entitlements_report(self):
        """Generate a report using the Subscription - Entitlement Report template.

        :id: 722e8802-367b-4399-bcaa-949daab26632

        :setup: Installed Satellite with Organization, Activation key,
                Content View, Content Host, and Subscriptions.

        :steps:

            1. Get
            /api/report_templates/130-Subscription - Entitlement Report/generate/id/report_format

        :expectedresults: Report is generated showing all necessary information for entitlements.

        :CaseImportance: High
        """
        with VirtualMachine(distro=DISTRO_RHEL7) as vm:
            vm.install_katello_ca()
            vm.register_contenthost(self.org_setup.label, self.ak_setup.name)
            assert vm.subscribed
            rt = (
                entities.ReportTemplate()
                .search(query={'search': 'name="Subscription - Entitlement Report"'})[0]
                .read()
            )
            res = rt.generate(
                data={
                    "organization_id": self.org_setup.id,
                    "report_format": "json",
                    "input_values": {"Days from Now": "no limit"},
                }
            )
            assert res[0]['Host Name'] == vm.hostname
            assert res[0]['Subscription Name'] == DEFAULT_SUBSCRIPTION_NAME

    @tier3
    @pytest.mark.usefixtures("setup_content")
    def test_positive_schedule_entitlements_report(self):
        """Schedule a report using the Subscription - Entitlement Report template.

        :id: 5152c518-b0da-4c27-8268-2be78289249f

        :setup: Installed Satellite with Organization, Activation key,
                Content View, Content Host, and Subscriptions.

        :steps:

            1. POST /api/report_templates/130-Subscription - Entitlement Report/schedule_report/

        :expectedresults: Report is scheduled and contains all necessary
                          information for entitlements.

        :CaseImportance: High
        """
        with VirtualMachine(distro=DISTRO_RHEL7) as vm:
            vm.install_katello_ca()
            vm.register_contenthost(self.org_setup.label, self.ak_setup.name)
            assert vm.subscribed
            rt = (
                entities.ReportTemplate()
                .search(query={'search': 'name="Subscription - Entitlement Report"'})[0]
                .read()
            )
            scheduled_csv = rt.schedule_report(
                data={
                    'id': '{}-Subscription - Entitlement Report'.format(rt.id),
                    'organization_id': self.org_setup.id,
                    'report_format': 'csv',
                    "input_values": {"Days from Now": "no limit"},
                }
            )
            data_csv = rt.report_data(data={'id': rt.id, 'job_id': scheduled_csv['job_id']})
            assert vm.hostname in data_csv
            assert DEFAULT_SUBSCRIPTION_NAME in data_csv
