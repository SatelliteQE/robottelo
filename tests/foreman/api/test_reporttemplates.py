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

from robottelo.decorators import tier1, tier2, stubbed
from robottelo.datafactory import valid_data_list
from robottelo.helpers import is_open
from robottelo.test import APITestCase

from fauxfactory import gen_string
from nailgun import entities
from requests import HTTPError


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
        res = entities.ReportTemplate().search(query={'search': u'name="{}"'.format(name)})
        self.assertIn(name, list(map(lambda x: x.name, res)))
        # Read
        rt = entities.ReportTemplate(id=rt.id).read()
        self.assertEqual(name, rt.name)
        self.assertEqual(template1, rt.template)
        # Update
        template2 = gen_string('alpha')
        entities.ReportTemplate(id=rt.id, template=template2).update(['template'])
        rt = entities.ReportTemplate(id=rt.id).read()
        self.assertEqual(template2, rt.template)
        # Delete
        entities.ReportTemplate(id=rt.id).delete()
        with self.assertRaises(HTTPError):
            rt = entities.ReportTemplate(id=rt.id).read()

    @tier1
    def test_positive_generate_report_nofilter(self):
        """Generate Host Status report

        :id: a4b687db-144e-4761-a42e-e93887464986

        :setup: User with reporting access rights, some report template, at least two hosts

        :steps:

            1. POST /api/report_templates/:id/generate

        :expectedresults: Report is generated for all hosts visible to user

        :CaseImportance: Critical
        """
        host_name = gen_string('alpha').lower()
        entities.Host(name=host_name).create()
        rt = entities.ReportTemplate().search(query={'search': u'name="Host statuses"'})[0].read()
        res = rt.generate()
        self.assertIn("Service Level", res)
        self.assertIn(host_name, res)

    @tier2
    def test_positive_generate_report_filter(self):
        """Generate Host Status report

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
        rt = entities.ReportTemplate().search(query={'search': u'name="Host statuses"'})[0].read()
        res = rt.generate(data={"input_values": {"hosts": host2_name}})
        self.assertIn("Service Level", res)
        self.assertNotIn(host1_name, res)
        self.assertIn(host2_name, res)

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
        entities.TemplateInput(name=input_name,
                               input_type="user",
                               template=rt.id,
                               ).create()
        ti = entities.TemplateInput(template=rt.id).search()[0].read()
        self.assertEquals(input_name, ti.name)
        res = rt.generate(data={"input_values": {input_name: input_value}})
        self.assertEquals('value="{}"'.format(input_value), res)

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
        self.assertTrue(rt.locked)
        # 3. Clone template, check cloned data
        rt.clone(data={'name': template_clone_name})
        cloned_rt = entities.ReportTemplate().search(
                  query={'search': u'name="{}"'.format(template_clone_name)})[0].read()
        self.assertEquals(template_clone_name, cloned_rt.name)
        self.assertEquals(template1, cloned_rt.template)
        # 4. Try to delete template
        if not is_open('BZ:1680458'):
            with self.assertRaises(HTTPError):
                rt.delete()
            # In BZ1680458, exception is thrown but template is deleted anyway
            self.assertNotEquals(0, len(entities.ReportTemplate().search(
                query={'search': u'name="{}"'.format(template_name)})))
        # 5. Try to edit template
        with self.assertRaises(HTTPError):
            entities.ReportTemplate(id=rt.id, template=template2).update(["template"])
        rt = rt.read()
        self.assertEquals(template1, rt.template)
        # 6. Unlock template
        entities.ReportTemplate(id=rt.id, locked=False).update(["locked"])
        rt = rt.read()
        self.assertFalse(rt.locked)
        # 7. Edit template
        entities.ReportTemplate(id=rt.id, template=template2).update(["template"])
        rt = rt.read()
        self.assertEquals(template2, rt.template)
        # 8. Delete template
        rt.delete()
        self.assertEquals(0, len(entities.ReportTemplate().search(
            query={'search': u'name="{}"'.format(template_name)})))

    @tier2
    @stubbed()
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
    @stubbed()
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
    @stubbed()
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
    @stubbed()
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
    @stubbed()
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
    @stubbed()
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
    @stubbed()
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
    @stubbed()
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
    @stubbed()
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
    @stubbed()
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
