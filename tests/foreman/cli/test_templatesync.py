"""Test class for Foreman Templates Import Export from CLI

:Requirement: TemplatesPlugin

:CaseAutomation: Automated

:CaseLevel: Integration

:CaseComponent: TemplatesPlugin

:Assignee: ogajduse

:TestType: Functional

:Upstream: No
"""
import pytest
from fauxfactory import gen_string
from nailgun import entities
from requests import get
from requests.exceptions import HTTPError

from robottelo import ssh
from robottelo.cli.template import Template
from robottelo.cli.template_sync import TemplateSync
from robottelo.constants import FOREMAN_TEMPLATE_IMPORT_URL
from robottelo.constants import FOREMAN_TEMPLATE_TEST_TEMPLATE


class TestTemplateSyncTestCase:
    @pytest.fixture(scope='module', autouse=True)
    def setUpClass(self):
        """Setup for TemplateSync functional testing

        :setup:

            1. Check if the the foreman templates custom repo and community templates repo is
            accessible.
            2. Download the example template in test running root dir to be used by tests

        Information:
            - https://theforeman.org/plugins/foreman_templates/5.0/index.html
            - /apidoc/v2/template/import.html
            - /apidoc/v2/template/export.html
            - http://pastebin.test.redhat.com/516304

        """
        # Check all Downloadable templates exists
        if not get(FOREMAN_TEMPLATE_IMPORT_URL).status_code == 200:
            raise HTTPError('The foreman templates git url is not accessible')

        # Download the Test Template in test running folder
        ssh.command(f'[ -f example_template.erb ] || wget {FOREMAN_TEMPLATE_TEST_TEMPLATE}')

    @pytest.mark.tier2
    def test_positive_import_force_locked_template(
        self, module_org, create_import_export_local_dir
    ):
        """Assure locked templates are updated from repository when `force` is
        specified.

        :id: b80fbfc4-bcab-4a5d-b6c1-0e22906cd8ab

        :Steps:
            1. Import some of the locked template specifying the `force`
               parameter `false`.
            2. After ensuring the template is not updated, Import same locked template
               specifying the `force` parameter `true`.

        :expectedresults:
            1. Assert result is {'message': 'success'}
            2. With force - false, assert that locked template is not updated.
            3. With force - true, assert that the locked template is updated.

        :CaseImportance: Medium

        :CaseAutomation: NotAutomated
        """
        prefix = gen_string('alpha')
        _, dir_path = create_import_export_local_dir
        TemplateSync.imports(
            {'repo': dir_path, 'prefix': prefix, 'organization-ids': module_org.id, 'lock': 'true'}
        )
        ptemplate = entities.ProvisioningTemplate().search(
            query={'per_page': 10, 'search': f'name~{prefix}', 'organization_id': module_org.id}
        )
        if ptemplate:
            assert ptemplate[0].read().locked
            update_txt = 'updated a little'
            ssh.command(f"echo {update_txt} >> {dir_path}/example_template.erb")
            TemplateSync.imports(
                {'repo': dir_path, 'prefix': prefix, 'organization-id': module_org.id}
            )
            assert update_txt not in Template.dump({'name': f'{prefix}example template'})
            TemplateSync.imports(
                {
                    'repo': dir_path,
                    'prefix': prefix,
                    'organization-id': module_org.id,
                    'force': 'true',
                }
            )
            assert update_txt in Template.dump({'name': f'{prefix}example template'})
        else:
            pytest.fail('The template is not imported for force test')

    @pytest.mark.stubbed
    @pytest.mark.tier2
    def test_positive_export_filtered_templates_to_git(self):
        """Assure only templates with a given filter regex are pushed to
        git template (new templates are created, existing updated).

        :id: fd583f85-f170-4b93-b9b1-36d72f31c31f

        :Steps:
            1. Export only the templates matching with regex e.g: `^atomic.*` to git repo.

        :expectedresults:
            1. Assert result is {'message': 'success'} and templates exported.
            2. Assert matching templates are exported to git repo.

        :CaseImportance: Critical

        :CaseAutomation: NotAutomated
        """

    @pytest.mark.tier2
    def test_positive_export_filtered_templates_to_temp_dir(self, module_org):
        """Assure templates can be exported to /tmp directory without right permissions

        :id: e0427ee8-698e-4868-952f-5f4723ccee87

        :bz: 1778177

        :Steps: Export the templates matching with regex e.g: `ansible` to /tmp directory.

        :expectedresults: The templates are exported /tmp directory

        :CaseImportance: Medium
        """
        dir_path = '/tmp'
        output = TemplateSync.exports(
            {'repo': dir_path, 'organization-id': module_org.id, 'filter': 'ansible'}
        )
        exported_count = [row == 'Exported: true' for row in output].count(True)
        assert exported_count == int(
            ssh.command(f'find {dir_path} -type f -name *ansible* | wc -l').stdout[0]
        )
