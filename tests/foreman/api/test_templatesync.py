"""Test class for Foreman Templates Import Export from API

:Requirement: TemplatesPlugin

:CaseAutomation: Automated

:CaseComponent: TemplatesPlugin

:Team: Endeavour

"""

import base64
import json
import time

from fauxfactory import gen_string
import pytest
import requests

from robottelo.config import settings
from robottelo.constants import (
    FOREMAN_TEMPLATE_IMPORT_API_URL,
    FOREMAN_TEMPLATE_IMPORT_URL,
    FOREMAN_TEMPLATE_ROOT_DIR,
    FOREMAN_TEMPLATE_TEST_TEMPLATE,
    FOREMAN_TEMPLATES_IMPORT_COUNT,
    FOREMAN_TEMPLATES_NOT_IMPORTED_COUNT,
)
from robottelo.logging import logger

git = settings.git


class TestTemplateSyncTestCase:
    """Implements TemplateSync tests from API"""

    @pytest.fixture(scope='module', autouse=True)
    def setUpClass(self, module_target_sat):
        """Setup for TemplateSync functional testing

        :setup:

            1. Check if the the foreman templates custom repo is accessible.
            2. Download the example template in test running root dir to be used by tests

        Information:
            - https://theforeman.org/plugins/foreman_templates/5.0/index.html
            - /apidoc/v2/template/import.html
            - /apidoc/v2/template/export.html
            - http://pastebin.test.redhat.com/516304

        """
        # Check all Downloadable templates exists
        if requests.get(FOREMAN_TEMPLATE_IMPORT_URL).status_code != 200:
            pytest.fail('The foreman templates git url is not accessible')

        # Download the Test Template in test running folder
        proxy_options = (
            f"-e use_proxy=yes -e https_proxy={settings.http_proxy.http_proxy_ipv6_url}"
            if not module_target_sat.network_type.has_ipv4
            else ""
        )
        module_target_sat.execute(
            f'[ -f example_template.erb ] || wget {proxy_options} {FOREMAN_TEMPLATE_TEST_TEMPLATE}'
        )

    def test_positive_import_filtered_templates_from_git(
        self, module_org, module_location, module_target_sat
    ):
        """Assure only templates with a given filter regex are pulled from
        git repo.

        :id: 628a95d6-7a4e-4e56-ad7b-d9fecd34f765

        :steps:
            1. Using nailgun or direct API call
               import only the templates matching with regex e.g: `^atomic.*`
               refer to: `/apidoc/v2/template/import.html`

        :expectedresults:
            1. Assert result is {'message': 'success'} and template imported
            2. Assert no other template has been imported but only those
               matching specified regex.
               NOTE: Templates are always imported with a prefix defaults to
               `community` unless it is specified as empty string
            3. Assert json output doesn't have
               'Name is not matching filter condition, skipping' info message
               for imported template

        :CaseImportance: High
        """
        prefix = gen_string('alpha')
        filtered_imported_templates = module_target_sat.api.Template().imports(
            data={
                'repo': FOREMAN_TEMPLATE_IMPORT_URL,
                'branch': 'automation',
                'filter': 'robottelo',
                'organization_ids': [module_org.id],
                'location_ids': [module_location.id],
                'prefix': prefix,
            }
        )
        imported_count = [
            template['imported'] for template in filtered_imported_templates['message']['templates']
        ].count(True)
        assert imported_count == 8
        ptemplates = module_target_sat.api.ProvisioningTemplate().search(
            query={
                'per_page': '100',
                'search': f'name~{prefix}',
                'organization_id': module_org.id,
                'location_id': module_location.id,
            }
        )
        assert len(ptemplates) == 5
        ptables = module_target_sat.api.PartitionTable().search(
            query={
                'per_page': '100',
                'search': f'name~{prefix}',
                'organization_id': module_org.id,
                'location_id': module_location.id,
            }
        )
        assert len(ptables) == 1
        jtemplates = module_target_sat.api.JobTemplate().search(
            query={
                'per_page': '100',
                'search': f'name~{prefix}',
                'organization_id': module_org.id,
                'location_id': module_location.id,
            }
        )
        assert len(jtemplates) == 1
        rtemplates = module_target_sat.api.ReportTemplate().search(
            query={
                'per_page': '10',
                'search': f'name~{prefix}',
                'organization_id': module_org.id,
                'location_id': module_location.id,
            }
        )
        assert len(rtemplates) == 1

    def test_import_filtered_templates_from_git_with_negate(self, module_org, module_target_sat):
        """Assure templates with a given filter regex are NOT pulled from
        git repo.

        :id: a6857454-249b-4a2e-9b53-b5d7b4eb34e3

        :steps:
            1. Using nailgun or direct API call
               import the templates NOT matching with regex e.g: `^freebsd.*`
               refer to: `/apidoc/v2/template/import.html` using the
               {'negate': true} in POST body to negate the filter regex.

        :expectedresults:
            1. Assert result is {'message': 'success'}
            2. Assert templates matching the regex were not pulled.

        :CaseImportance: Medium
        """
        prefix = gen_string('alpha')
        filtered_imported_templates = module_target_sat.api.Template().imports(
            data={
                'repo': FOREMAN_TEMPLATE_IMPORT_URL,
                'branch': 'automation',
                'filter': 'robottelo',
                'organization_ids': [module_org.id],
                'prefix': prefix,
                'negate': True,
            }
        )
        not_imported_count = [
            template['imported'] for template in filtered_imported_templates['message']['templates']
        ].count(False)
        exp_not_imported_count = (
            FOREMAN_TEMPLATES_NOT_IMPORTED_COUNT["PUPPET_ENABLED"]
            if "puppet" in module_target_sat.get_features()
            else FOREMAN_TEMPLATES_NOT_IMPORTED_COUNT["PUPPET_DISABLED"]
        )
        assert not_imported_count == exp_not_imported_count
        ptemplates = module_target_sat.api.ProvisioningTemplate().search(
            query={'per_page': '100', 'search': 'name~jenkins', 'organization_id': module_org.id}
        )
        assert len(ptemplates) == 6
        ptables = module_target_sat.api.PartitionTable().search(
            query={'per_page': '100', 'search': 'name~jenkins', 'organization_id': module_org.id}
        )
        assert len(ptables) == 1
        rtemplates = module_target_sat.api.ReportTemplate().search(
            query={'per_page': '100', 'search': 'name~jenkins', 'organization_id': module_org.id}
        )
        assert len(rtemplates) == 1

    def test_import_template_with_puppet(self, parametrized_puppet_sat):
        """Importing puppet templates with enabled/disabled puppet module

        :steps:
            1. Have enabled(disabled) puppet module
            2. Import template containing puppet
            3. Check if template was imported

        :expectedresults:
            Template was (not) imported

        :id: 9ab46883-a3a7-4d2c-9a79-3d574bfd2ad8

        :parametrized: yes

        :CaseImportance: Medium
        """
        prefix = gen_string('alpha')
        api_template = parametrized_puppet_sat['sat'].api.Template()
        filtered_imported_templates = api_template.imports(
            data={
                'repo': FOREMAN_TEMPLATE_IMPORT_URL,
                'branch': 'automation',
                'dirname': 'import/job_templates/',
                'filter': 'jenkins Start OpenSCAP scans',
                'force': True,
                'prefix': prefix,
            }
        )
        not_imported_count = [
            template['imported'] for template in filtered_imported_templates['message']['templates']
        ].count(False)
        if parametrized_puppet_sat['enabled']:
            assert not_imported_count == 1
        else:
            assert not_imported_count == 2

    def test_positive_import_and_associate(
        self,
        create_import_export_local_dir,
        module_location,
        module_org,
        default_org,
        default_location,
        target_sat,
    ):
        """Assure imported templates are associated/not_associated with taxonomies based on
        `associate` option and templates metadata.

        :id: 04a14a56-bd71-412b-b2da-4b8c3991c401

        :steps:
            1. Create new taxonomies, lets say org X and loc Y.
            2. From X and Y taxonomies scope, Import template1 as associate 'never', where the
                template contains the metadata anything other than X and Y taxonomies.
            3. Create new template2 in the importing source.
            4. From X and Y taxonomies scope, Import template 1 and 2 as associate 'new',
                where the template contains the metadata anything other than X and Y taxonomies.
            5. From X and Y taxonomies scope, Import template 1 and 2 as associate 'always',
                where the template contains the metadata anything other than X and Y taxonomies.

        :expectedresults:
            1. with Associate Never, templates are imported in importing taxonomies
            2. with Associate Never, templates are not imported in metadata taxonomies
            3. with Associate New, on reimporting the existing templates, taxonomies
                are not changed to metadata taxonomies
            4. with Associate New, new templates are imported in importing taxonomies
                even though importing taxonomies are not part of metadata taxonomies
            5. with Associate Always, all the existing and new templates are imported in importing
                taxonomies even though importing taxonomies are not part of metadata taxonomies

        :CaseImportance: Medium
        """
        prefix = gen_string('alpha')
        _, dir_path = create_import_export_local_dir
        # Associate Never
        target_sat.api.Template().imports(
            data={
                'repo': dir_path,
                'prefix': prefix,
                'organization_ids': [module_org.id],
                'location_ids': [module_location.id],
                'associate': 'never',
            }
        )
        # - Template 1 imported in X and Y taxonomies
        ptemplate = target_sat.api.ProvisioningTemplate().search(
            query={
                'per_page': '10',
                'search': f'name~{prefix}',
                'organization_id': module_org.id,
                'location_id': module_location.id,
            }
        )
        assert ptemplate
        assert len(ptemplate[0].read().organization) == 1
        # - Template 1 not imported in metadata taxonomies
        ptemplate = target_sat.api.ProvisioningTemplate().search(
            query={
                'per_page': '10',
                'search': f'name~{prefix}',
                'organization_id': default_org.id,
                'location_id': default_location.id,
            }
        )
        assert not ptemplate
        # Associate New
        target_sat.execute(
            f'cp {dir_path}/example_template.erb {dir_path}/another_template.erb && '
            f'sed -ie "s/name: .*/name: another_template/" {dir_path}/another_template.erb'
        )
        target_sat.api.Template().imports(
            data={
                'repo': dir_path,
                'prefix': prefix,
                'organization_ids': [module_org.id],
                'location_ids': [module_location.id],
                'associate': 'new',
            }
        )
        # - Template 1 taxonomies are not changed
        ptemplate = target_sat.api.ProvisioningTemplate().search(
            query={
                'per_page': '10',
                'search': f'name~{prefix}example_template',
                'organization_id': module_org.id,
                'location_id': module_location.id,
            }
        )
        assert ptemplate
        assert len(ptemplate[0].read().organization) == 1
        # - Template 2 should be imported in importing taxonomies
        ptemplate = target_sat.api.ProvisioningTemplate().search(
            query={
                'per_page': '10',
                'search': f'name~{prefix}another_template',
                'organization_id': module_org.id,
                'location_id': module_location.id,
            }
        )
        assert ptemplate
        assert len(ptemplate[0].read().organization) == 1
        # Associate Always
        target_sat.api.Template().imports(
            data={
                'repo': dir_path,
                'prefix': prefix,
                'organization_ids': [module_org.id],
                'location_ids': [module_location.id],
                'associate': 'always',
            }
        )
        # - Template 1 taxonomies are not changed
        ptemplate = target_sat.api.ProvisioningTemplate().search(
            query={
                'per_page': '10',
                'search': f'name~{prefix}example_template',
                'organization_id': module_org.id,
                'location_id': module_location.id,
            }
        )
        assert ptemplate
        assert len(ptemplate[0].read().organization) == 1
        # - Template 2 taxonomies are not changed
        ptemplate = target_sat.api.ProvisioningTemplate().search(
            query={
                'per_page': '10',
                'search': f'name~{prefix}another_template',
                'organization_id': module_org.id,
                'location_id': module_location.id,
            }
        )
        assert ptemplate
        assert len(ptemplate[0].read().organization) == 1

    def test_positive_import_from_subdirectory(self, module_org, module_target_sat):
        """Assure templates are imported from specific repositories subdirectory

        :id: 8ea11a1a-165e-4834-9387-7accb4c94e77

        :steps:
            1. Using nailgun or direct API call
               import templates specifying a git subdirectory e.g:
               `-d {'dirname': 'test_sub_dir'}` in POST body

        :expectedresults:
            1. Assert result is {'message': 'success'} and templates imported
            2. Assert templates are imported only from given subdirectory

        :CaseImportance: Medium
        """
        prefix = gen_string('alpha')
        filtered_imported_templates = module_target_sat.api.Template().imports(
            data={
                'repo': FOREMAN_TEMPLATE_IMPORT_URL,
                'branch': 'automation',
                'dirname': 'import/report_templates',
                'organization_ids': [module_org.id],
                'prefix': prefix,
            }
        )
        imported_count = [
            template['imported'] for template in filtered_imported_templates['message']['templates']
        ].count(True)
        # check name of imported temp
        assert imported_count == 2

    # Export tests

    def test_positive_export_filtered_templates_to_localdir(
        self, module_org, create_import_export_local_dir, target_sat
    ):
        """Assure only templates with a given filter regex are pushed to
        local directory (new templates are created, existing updated).

        :id: b7c98b75-4dd1-4b6a-b424-35b0f48c25db

        :steps:
            1. Using nailgun or direct API call
               export only the templates matching with regex e.g: `robottelo`
               refer to: `/apidoc/v2/template/export.html`

        :expectedresults:
            1. Assert result is {'message': 'success'} and templates exported.
            2. Assert no other template has been exported but only those
               matching specified regex.

        :CaseImportance: Low
        """
        dir_name, dir_path = create_import_export_local_dir
        exported_temps = target_sat.api.Template().exports(
            data={
                'repo': FOREMAN_TEMPLATE_ROOT_DIR,
                'dirname': dir_name,
                'organization_ids': [module_org.id],
                'filter': 'ansible',
            }
        )
        exported_count = [
            template['exported'] for template in exported_temps['message']['templates']
        ].count(True)
        assert exported_count == int(
            target_sat.execute(f'find {dir_path} -type f -name *ansible* | wc -l').stdout.strip()
        )

    def test_positive_export_filtered_templates_negate(
        self, module_org, create_import_export_local_dir, target_sat
    ):
        """Assure templates with a given filter regex are not exported.

        :id: 2f8ad8f3-f02b-4b2d-85af-423a228976f3

        :steps:
            1. Using nailgun or direct API call
               export templates matching that does not matches regex e.g: `robottelo`
               using `negate` option.


        :expectedresults:
            1. Assert templates other than `robottelo` has been exported.

        :CaseImportance: Medium
        """
        # Export some filtered templates to local dir
        _, dir_path = create_import_export_local_dir
        target_sat.api.Template().exports(
            data={
                'repo': dir_path,
                'organization_ids': [module_org.id],
                'filter': 'ansible',
                'negate': True,
            }
        )
        assert (
            target_sat.execute(f'find {dir_path} -type f -name *ansible* | wc -l').stdout.strip()
            == '0'
        )
        assert target_sat.execute(f'find {dir_path} -type f | wc -l').stdout.strip() != '0'

    def test_positive_export_and_import_with_metadata(
        self, create_import_export_local_dir, module_org, module_location, target_sat
    ):
        """Assure exported template contains metadata.

        :id: ba8a34ce-c2c6-4889-8729-59714c0a4b19

        :steps:
            1. Create a template in local directory and specify Org/Loc.
            2. Use import to pull this specific template (using filter).
            3. Using nailgun or direct API call
               export the template containing metadata with Org/Loc specs
               and specify the `metadata_export_mode` parameter
               e.g: `-d {'metadata_export_mode': 'refresh'}` in POST body

        :expectedresults:
            1. Assert template is exported and new org/loc are present on
               template metadata

        :CaseImportance: Medium
        """
        ex_template = 'example_template.erb'
        prefix = gen_string('alpha')
        _, dir_path = create_import_export_local_dir
        target_sat.api.Template().imports(
            data={
                'repo': dir_path,
                'location_ids': [module_location.id],
                'organization_ids': [module_org.id],
                'prefix': prefix,
            }
        )
        export_file = f'{prefix.lower()}{ex_template}'
        # Export same template to local dir with refreshed metadata
        target_sat.api.Template().exports(
            data={
                'metadata_export_mode': 'refresh',
                'repo': dir_path,
                'location_ids': [module_location.id],
                'organization_ids': [module_org.id],
                'filter': prefix,
            }
        )
        result = target_sat.execute(
            f'grep {module_org.name} {dir_path}/provisioning_templates/user_data/{export_file}'
        )
        assert result.status == 0
        # Export same template to local dir with keeping metadata
        target_sat.api.Template().exports(
            data={
                'metadata_export_mode': 'keep',
                'repo': dir_path,
                'organization_ids': [module_org.id],
                'location_ids': [module_location.id],
                'filter': prefix,
            }
        )
        result = target_sat.execute(
            f'grep {module_org.name} {dir_path}/provisioning_templates/user_data/{export_file}'
        )
        assert result.status == 1
        # Export same template to local dir with removed metadata
        target_sat.api.Template().exports(
            data={
                'metadata_export_mode': 'remove',
                'repo': dir_path,
                'organization_ids': [module_org.id],
                'location_ids': [module_location.id],
                'filter': prefix,
            }
        )
        result = target_sat.execute(
            f'grep organizations: {dir_path}/provisioning_templates/user_data/{export_file}'
        )
        assert result.status == 1

    # Take Templates out of Tech Preview Feature Tests
    @pytest.mark.parametrize('verbose', [True, False])
    def test_positive_import_json_output_verbose(self, module_org, verbose, module_target_sat):
        """Assert all the required fields displayed in import output when
        verbose is True and False

        :id: 74b0a701-341f-4062-9769-e5cb1a1c4792

        :steps:
            1. Using nailgun or direct API call
               Import a template with verbose `True` and `False` option

        :expectedresults:
            1. Assert json output has all the following fields
               'name', 'imported', 'diff', 'additional_errors', 'exception',
               'validation_errors', 'file'

        :Requirement: Take Templates out of tech preview

        :parametrized: yes

        :CaseImportance: Low
        """
        prefix = gen_string('alpha')
        templates = module_target_sat.api.Template().imports(
            data={
                'repo': FOREMAN_TEMPLATE_IMPORT_URL,
                'branch': 'master',
                'filter': 'robottelo',
                'organization_ids': [module_org.id],
                'prefix': prefix,
                'verbose': verbose,
            }
        )
        expected_fields = [
            'name',
            'imported',
            'additional_errors',
            'exception',
            'validation_errors',
            'file',
            'type',
            'id',
            'changed',
            'additional_info',
        ]
        if verbose:
            expected_fields.append('diff')
        actual_fields = templates['message']['templates'][0].keys()
        assert sorted(actual_fields) == sorted(expected_fields)

    def test_positive_import_json_output_changed_key_true(
        self, create_import_export_local_dir, module_org, target_sat
    ):
        """Assert template imports output `changed` key returns `True` when
        template data gets updated

        :id: 4b866144-822c-4786-9188-53bc7e2dd44a

        :steps:
            1. Using nailgun or direct API call
               Create a template and import it from a source
            2. Update the template data in source location
            3. Using nailgun or direct API call
               Re-import the same template

        :expectedresults:
            1. On reimport, Assert json output returns 'changed' as `true`
            2. Assert json output returns diff key with difference as value

        :Requirement: Take Templates out of tech preview

        :CaseImportance: Low
        """
        prefix = gen_string('alpha')
        _, dir_path = create_import_export_local_dir
        pre_template = target_sat.api.Template().imports(
            data={'repo': dir_path, 'organization_ids': [module_org.id], 'prefix': prefix}
        )
        assert bool(pre_template['message']['templates'][0]['imported'])
        target_sat.execute(f'echo " Updating Template data." >> {dir_path}/example_template.erb')
        post_template = target_sat.api.Template().imports(
            data={'repo': dir_path, 'organization_ids': [module_org.id], 'prefix': prefix}
        )
        assert bool(post_template['message']['templates'][0]['changed'])

    def test_positive_import_json_output_changed_key_false(
        self, create_import_export_local_dir, module_org, module_target_sat
    ):
        """Assert template imports output `changed` key returns `False` when
        template data gets updated

        :id: 64456c0c-c2c6-4a1c-a16e-54ca4a8b66d3

        :steps:
            1. Using nailgun or direct API call
               Create a template and import it from a source
            2. Dont update the template data in source location
            3. Using nailgun or direct API call
               Re-import the same template

        :expectedresults:
            1. On reiport, Assert json output returns 'changed' as `false`

        :Requirement: Take Templates out of tech preview

        :CaseImportance: Low
        """
        prefix = gen_string('alpha')
        _, dir_path = create_import_export_local_dir
        pre_template = module_target_sat.api.Template().imports(
            data={'repo': dir_path, 'organization_ids': [module_org.id], 'prefix': prefix}
        )
        assert bool(pre_template['message']['templates'][0]['imported'])
        post_template = module_target_sat.api.Template().imports(
            data={'repo': dir_path, 'organization_ids': [module_org.id], 'prefix': prefix}
        )
        assert not bool(post_template['message']['templates'][0]['changed'])

    def test_positive_import_json_output_name_key(
        self, create_import_export_local_dir, module_org, target_sat
    ):
        """Assert template imports output `name` key returns correct name

        :id: a5639368-3d23-4a37-974a-889e2ec0916e

        :steps:
            1. Using nailgun or direct API call
               Create a template with some name and import it from a source

        :expectedresults:
            1. On Import, Assert json output returns 'name' key with correct
            name as per template metadata

        :Requirement: Take Templates out of tech preview

        :CaseImportance: Low
        """
        template_name = gen_string('alpha')
        _, dir_path = create_import_export_local_dir
        target_sat.execute(
            f'sed -ie "s/name: .*/name: {template_name}/" {dir_path}/example_template.erb'
        )
        template = target_sat.api.Template().imports(
            data={'repo': dir_path, 'organization_ids': [module_org.id]}
        )
        assert 'name' in template['message']['templates'][0]
        assert template_name == template['message']['templates'][0]['name']

    def test_positive_import_json_output_imported_key(
        self, create_import_export_local_dir, module_org, module_target_sat
    ):
        """Assert template imports output `imported` key returns `True` on
        successful import

        :id: 5bc11163-e8f3-4744-8a76-5c16e6e46e86

        :steps:
            1. Using nailgun or direct API call
               Create a template and import it from a source

        :expectedresults:
            1. On Import, Assert json output returns 'imported' key as `True`

        :Requirement: Take Templates out of tech preview

        :CaseImportance: Low
        """
        prefix = gen_string('alpha')
        _, dir_path = create_import_export_local_dir
        template = module_target_sat.api.Template().imports(
            data={'repo': dir_path, 'organization_ids': [module_org.id], 'prefix': prefix}
        )
        assert bool(template['message']['templates'][0]['imported'])

    def test_positive_import_json_output_file_key(
        self, create_import_export_local_dir, module_org, module_target_sat
    ):
        """Assert template imports output `file` key returns correct file name
        from where the template is imported

        :id: da0b094c-6dc8-4526-b115-8e08bfb05fbb

        :steps:
            1. Using nailgun or direct API call
               Create a template with some name and import it from a source

        :expectedresults:
            1. Assert json output returns 'file' key with correct
            file name

        :Requirement: Take Templates out of tech preview

        :CaseImportance: Low
        """
        _, dir_path = create_import_export_local_dir
        template = module_target_sat.api.Template().imports(
            data={'repo': dir_path, 'organization_ids': [module_org.id]}
        )
        assert template['message']['templates'][0]['file'] == 'example_template.erb'

    def test_positive_import_json_output_corrupted_metadata(
        self, create_import_export_local_dir, module_org, target_sat
    ):
        """Assert template imports output returns corrupted metadata error for
        incorrect metadata in template

        :id: 6bd5bc6b-a7a2-4529-9df6-47a670cd86d8

        :steps:
            1. Create a template with wrong syntax in metadata
            2. Using nailgun or direct API call
               Import above template

        :expectedresults:
            1. Assert json output has error contains
            'Failed to parse metadata' text
            2. Assert 'imported' key returns 'false' value

        :Requirement: Take Templates out of tech preview

        :CaseImportance: Medium
        """
        _, dir_path = create_import_export_local_dir
        target_sat.execute(f'sed -ie "s/<%#/$#$#@%^$^@@RT$$/" {dir_path}/example_template.erb')
        template = target_sat.api.Template().imports(
            data={'repo': dir_path, 'organization_ids': [module_org.id]}
        )
        assert not bool(template['message']['templates'][0]['imported'])
        assert (
            template['message']['templates'][0]['additional_errors'] == 'Failed to parse metadata'
        )

    def test_positive_import_json_output_filtered_skip_message(
        self, create_import_export_local_dir, module_org, module_target_sat
    ):
        """Assert template imports output returns template import skipped info
        for templates whose name doesn't match the filter

        :id: db68b5de-7647-4568-b79c-2aec3292328a

        :steps:
            1. Using nailgun or direct API call
               Create template with name not matching filter

        :expectedresults:
            1. Assert json output has info contains
            'Name is not matching filter condition, skipping' text
            2. Assert 'imported' key returns 'false' value

        :Requirement: Take Templates out of tech preview

        :CaseImportance: Low
        """
        _, dir_path = create_import_export_local_dir
        template = module_target_sat.api.Template().imports(
            data={
                'repo': dir_path,
                'organization_ids': [module_org.id],
                'filter': gen_string('alpha'),
            }
        )
        assert not bool(template['message']['templates'][0]['imported'])
        assert (
            template['message']['templates'][0]['additional_info']
            == "Skipping, 'name' filtered out based on 'filter' and 'negate' settings"
        )

    def test_positive_import_json_output_no_name_error(
        self, create_import_export_local_dir, module_org, target_sat
    ):
        """Assert template imports output returns no name error for template
        without name

        :id: 259a8a3a-8749-442d-a2bc-51e9af89ce8c

        :steps:
            1. Create a template without name in metadata
            2. Using nailgun or direct API call
               Import above template

        :expectedresults:
            1. Assert json output has error contains
            'No 'name' found in metadata' text
            2. Assert 'imported' key returns 'false' value

        :Requirement: Take Templates out of tech preview

        :CaseImportance: Low
        """
        _, dir_path = create_import_export_local_dir
        target_sat.execute(f'sed -ie "s/name: .*/name: /" {dir_path}/example_template.erb')
        template = target_sat.api.Template().imports(
            data={'repo': dir_path, 'organization_ids': [module_org.id]}
        )
        assert not bool(template['message']['templates'][0]['imported'])
        assert (
            template['message']['templates'][0]['additional_errors']
            == "No 'name' found in metadata"
        )

    def test_positive_import_json_output_no_model_error(
        self, create_import_export_local_dir, module_org, target_sat
    ):
        """Assert template imports output returns no model error for template
        without model

        :id: d3f1ffe4-58d7-45a8-b278-74e081dc5062

        :steps:
            1. Create a template without model keyword in metadata
            2. Using nailgun or direct API call
               Import above template

        :expectedresults:
            1. Assert json output has error contains
            'No 'model' found in metadata' text
            2. Assert 'imported' key returns 'false' value

        :Requirement: Take Templates out of tech preview

        :CaseImportance: Low
        """
        _, dir_path = create_import_export_local_dir
        target_sat.execute(f'sed -ie "/model: .*/d" {dir_path}/example_template.erb')
        template = target_sat.api.Template().imports(
            data={'repo': dir_path, 'organization_ids': [module_org.id]}
        )
        assert not bool(template['message']['templates'][0]['imported'])
        assert (
            template['message']['templates'][0]['additional_errors']
            == "No 'model' found in metadata"
        )

    def test_positive_import_json_output_blank_model_error(
        self, create_import_export_local_dir, module_org, target_sat
    ):
        """Assert template imports output returns blank model name error for
        template without template name

        :id: 5007b12d-1cf6-49e6-8e54-a189d1a209de

        :steps:
            1. Create a template with blank model name in metadata
            2. Using nailgun or direct API call
               Import above template

        :expectedresults:
            1. Assert json output has additional_error contains
               'Template type was not found, maybe you are missing a plugin?'
            2. Assert 'imported' key returns 'false' value

        :Requirement: Take Templates out of tech preview

        :CaseImportance: Low
        """
        _, dir_path = create_import_export_local_dir
        target_sat.execute(f'sed -ie "s/model: .*/model: /" {dir_path}/example_template.erb')
        template = target_sat.api.Template().imports(
            data={'repo': dir_path, 'organization_ids': [module_org.id]}
        )
        assert not bool(template['message']['templates'][0]['imported'])
        assert (
            template['message']['templates'][0]['additional_errors']
            == "Template type  was not found, are you missing a plugin?"
        )

    def test_positive_export_json_output(
        self, create_import_export_local_dir, module_org, target_sat
    ):
        """Assert template export output returns template names

        :id: 141b893d-72a3-47c2-bb03-004c757bcfc9

        :steps:
            1. Using nailgun or direct API call
               Export all the templates

        :expectedresults:
            1. Assert json output has all the exported template names
            and typewise

        :Requirement: Take Templates out of tech preview

        :CaseImportance: Low
        """
        prefix = gen_string('alpha')
        imported_templates = target_sat.api.Template().imports(
            data={
                'repo': FOREMAN_TEMPLATE_IMPORT_URL,
                'branch': 'automation',
                'organization_ids': [module_org.id],
                'prefix': prefix,
                'dirname': 'import',
            }
        )
        imported_count = [
            template['imported'] for template in imported_templates['message']['templates']
        ].count(True)
        exp_count = (
            FOREMAN_TEMPLATES_IMPORT_COUNT["PUPPET_ENABLED"]
            if "puppet" in target_sat.get_features()
            else FOREMAN_TEMPLATES_IMPORT_COUNT["PUPPET_DISABLED"]
        )
        assert imported_count == exp_count  # Total Count
        # Export some filtered templates to local dir
        _, dir_path = create_import_export_local_dir
        exported_templates = target_sat.api.Template().exports(
            data={'repo': dir_path, 'organization_ids': [module_org.id], 'filter': prefix}
        )
        exported_count = [
            template['exported'] for template in exported_templates['message']['templates']
        ].count(True)
        assert exported_count == exp_count
        assert 'name' in exported_templates['message']['templates'][0]
        assert (
            target_sat.execute(
                f'[ -d {dir_path}/job_templates ] && '
                f'[ -d {dir_path}/partition_tables_templates ] && '
                f'[ -d {dir_path}/provisioning_templates ] && '
                f'[ -d {dir_path}/report_templates ]'
            ).status
            == 0
        )

    def test_positive_import_log_to_production(self, module_org, target_sat):
        """Assert template import logs are logged to production logs

        :id: 19ed0e6a-ee77-4e28-86c9-49db1adec479

        :steps:
            1. Using nailgun or direct API call
               Import template from a source

        :expectedresults:
            1. Assert template import task and status logged to production log

        :Requirement: Take Templates out of tech preview

        :CaseImportance: Low
        """
        target_sat.api.Template().imports(
            data={
                'repo': FOREMAN_TEMPLATE_IMPORT_URL,
                'branch': 'master',
                'organization_ids': [module_org.id],
                'filter': 'empty',
            }
        )
        time.sleep(5)
        assert (
            target_sat.execute(
                'grep -i \'Started POST "/api/v2/templates/import"\''
                ' /var/log/foreman/production.log'
            ).status
            == 0
        )

    def test_positive_export_log_to_production(
        self, create_import_export_local_dir, module_org, target_sat
    ):
        """Assert template export logs are logged to production logs

        :id: 8ae370b1-84e8-436e-a7d7-99cd0b8f45b1

        :steps:
            1. Using nailgun or direct API call
               Export template to destination

        :expectedresults:
            1. Assert template export task and status logged to production log

        :Requirement: Take Templates out of tech preview

        :CaseImportance: Low
        """
        target_sat.api.Template().imports(
            data={
                'repo': FOREMAN_TEMPLATE_IMPORT_URL,
                'branch': 'master',
                'organization_ids': [module_org.id],
                'filter': 'empty',
            }
        )
        _, dir_path = create_import_export_local_dir
        target_sat.api.Template().exports(
            data={'repo': dir_path, 'organization_ids': [module_org.id], 'filter': 'empty'}
        )
        time.sleep(5)
        assert (
            target_sat.execute(
                'grep -i \'Started POST "/api/v2/templates/export"\''
                ' /var/log/foreman/production.log'
            ).status
            == 0
        )

    @pytest.mark.skip_if_not_set('git')
    @pytest.mark.parametrize(
        ('url', 'git_repository', 'use_proxy', 'setup_http_proxy_without_global_settings'),
        [
            (
                f'http://{git.username}:{git.password}@{git.hostname}:{git.http_port}',
                True,
                True,
                True,
            ),
            (
                f'http://{git.username}:{git.password}@{git.hostname}:{git.http_port}',
                True,
                True,
                False,
            ),
            (
                f'http://{git.username}:{git.password}@{git.hostname}:{git.http_port}',
                True,
                False,
                True,
            ),
            (
                f'http://{git.username}:{git.password}@{git.hostname}:{git.http_port}',
                False,
                True,
                True,
            ),
            (
                f'http://{git.username}:{git.password}@{git.hostname}:{git.http_port}',
                False,
                False,
                True,
            ),
            (
                f'http://{git.username}:{git.password}@{git.hostname}:{git.http_port}',
                False,
                True,
                False,
            ),
            (f'ssh://git@{git.hostname}:{git.ssh_port}', True, False, True),
            (f'ssh://git@{git.hostname}:{git.ssh_port}', False, False, True),
        ],
        ids=[
            'auth_http_proxy-use_proxy-non_empty_repo-http',
            'unauth_http_proxy-use_proxy-non_empty_repo-http',
            'auth_http_proxy-do_not_use_proxy-non_empty_repo-http',
            'auth_http_proxy-use_proxy-empty_repo-http',
            'auth_http_proxy-do_not_use_proxy-empty_repo-http',
            'unauth_http_proxy-use_proxy-empty_repo-http',
            'auth_http_proxy-do_not_use_proxy-non_empty_repo-ssh',
            'auth_http_proxy-do_not_use_proxy-empty_repo-ssh',
        ],
        indirect=['git_repository', 'setup_http_proxy_without_global_settings'],
    )
    def test_positive_export_all_templates_to_repo(
        self,
        module_org,
        git_repository,
        git_branch,
        url,
        module_target_sat,
        use_proxy,
        setup_http_proxy_without_global_settings,
    ):
        """Assure all templates are exported if no filter is specified.

        :id: 0bf6fe77-01a3-4843-86d6-22db5b8adf3b

        :setup:
            1. If using proxy, disable direct connection to the git instance

        :steps:
            1. Using nailgun export all templates to repository (ensure filters are empty)

        :expectedresults:
            1. Assert all existing templates were exported to repository

        :BZ: 1785613

        :parametrized: yes

        :CaseImportance: Low
        """
        proxy, _ = setup_http_proxy_without_global_settings
        try:
            data = {
                'repo': f'{url}/{git.username}/{git_repository["name"]}',
                'branch': git_branch,
                'organization_ids': [module_org.id],
            }
            if use_proxy:
                proxy_hostname = proxy.url.split('/')[2].split(':')[0]
                old_log = module_target_sat.cutoff_host_setup_log(
                    proxy_hostname, settings.git.hostname
                )
                data['http_proxy_policy'] = 'selected'
                data['http_proxy_id'] = proxy.id
            output = module_target_sat.api.Template().exports(data=data)
            auth = (git.username, git.password)
            api_url = f'http://{git.hostname}:{git.http_port}/api/v1/repos/{git.username}'
            res = requests.get(
                url=f'{api_url}/{git_repository["name"]}/git/trees/{git_branch}',
                auth=auth,
                params={'recursive': True},
            )
            res.raise_for_status()
        finally:
            if use_proxy:
                module_target_sat.restore_host_check_log(
                    proxy_hostname, settings.git.hostname, old_log
                )

        try:
            tree = json.loads(res.text)['tree']
        except json.decoder.JSONDecodeError:
            logger.debug(res.json())
            pytest.fail(f"Failed to parse output from git. Response: '{res.text}'")
        git_count = [row['path'].endswith('.erb') for row in tree].count(True)
        assert len(output['message']['templates']) == git_count

    def test_positive_import_all_templates_from_repo(self, module_org, module_target_sat):
        """Assure all templates are imported if no filter is specified.

        :id: 95ac9543-d989-44f4-b4d9-18f20a0b58b9

        :steps:
            1. Using nailgun import all templates from repository (ensure filters are empty)

        :expectedresults:
            1. Assert all existing templates are imported.

        :CaseImportance: Low
        """
        output = module_target_sat.api.Template().imports(
            data={
                'repo': FOREMAN_TEMPLATE_IMPORT_URL,
                'branch': 'master',
                'organization_ids': [module_org.id],
                'filter': '',
            }
        )
        res = requests.get(
            url=f"{FOREMAN_TEMPLATE_IMPORT_API_URL}/git/trees/master",
            headers={'Authorization': f'token {settings.git.github_token}'},
            params={'recursive': True},
        )
        res.raise_for_status()
        tree = json.loads(res.text)['tree']
        git_count = [row['path'].endswith('.erb') for row in tree].count(True)
        assert len(output['message']['templates']) == git_count

    def test_negative_import_locked_template(self, module_org, module_target_sat):
        """Assure locked templates are not pulled from repository.

        :id: 88e21cad-448e-45e0-add2-94493a1319c5

        :steps:
            1. Using nailgun try to import a locked template

        :expectedresults:
            1. Assert locked template is not updated

        :CaseImportance: Medium
        """
        # import template with lock
        output = module_target_sat.api.Template().imports(
            data={
                'repo': FOREMAN_TEMPLATE_IMPORT_URL,
                'branch': 'locked',
                'organization_ids': [module_org.id],
                'dirname': 'locked',
                'force': True,
                'lock': True,
            }
        )
        assert output['message']['templates'][0]['imported']
        # try to import same template with changed content
        output = module_target_sat.api.Template().imports(
            data={
                'repo': FOREMAN_TEMPLATE_IMPORT_URL,
                'branch': 'locked',
                'organization_ids': [module_org.id],
                'dirname': 'after_lock',
            }
        )
        # assert content wasn't changed
        assert not output['message']['templates'][0]['imported']
        res = requests.get(
            url=f"{FOREMAN_TEMPLATE_IMPORT_API_URL}/contents/locked/robottelo_locked.erb",
            headers={'Authorization': f'token {settings.git.github_token}'},
            params={'ref': 'locked'},
        )
        res.raise_for_status()
        git_content = base64.b64decode(json.loads(res.text)['content'])
        sat_content = module_target_sat.api.ProvisioningTemplate(
            id=output['message']['templates'][0]['id']
        ).read()
        assert git_content.decode('utf-8') == sat_content.template

    def test_positive_import_locked_template(self, module_org, module_target_sat):
        """Assure locked templates are pulled from repository while using force parameter.

        :id: 936c91cc-1947-45b0-8bf0-79ba4be87b97

        :steps:
            1. Using nailgun try to import a locked template with force parameter

        :expectedresults:
            1. Assert locked template is updated

        :CaseImportance: Medium
        """
        # import template with lock
        output = module_target_sat.api.Template().imports(
            data={
                'repo': FOREMAN_TEMPLATE_IMPORT_URL,
                'branch': 'locked',
                'organization_ids': [module_org.id],
                'dirname': 'locked',
                'force': True,
                'lock': True,
            }
        )
        assert output['message']['templates'][0]['imported']
        # force import same template with changed content
        output = module_target_sat.api.Template().imports(
            data={
                'repo': FOREMAN_TEMPLATE_IMPORT_URL,
                'branch': 'locked',
                'organization_ids': [module_org.id],
                'dirname': 'after_lock',
                'force': True,
            }
        )
        # assert template was changed
        assert output['message']['templates'][0]['imported']
        assert output['message']['templates'][0]['changed']
        res = requests.get(
            url=f"{FOREMAN_TEMPLATE_IMPORT_API_URL}/contents/after_lock/robottelo_locked.erb",
            headers={'Authorization': f'token {settings.git.github_token}'},
            params={'ref': 'locked'},
        )
        res.raise_for_status()
        git_content = base64.b64decode(json.loads(res.text)['content'])
        sat_content = module_target_sat.api.ProvisioningTemplate(
            id=output['message']['templates'][0]['id']
        ).read()
        assert git_content.decode('utf-8') == sat_content.template
