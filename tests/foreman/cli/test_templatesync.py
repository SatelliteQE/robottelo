"""Test class for Foreman Templates Import Export from CLI

:Requirement: TemplatesPlugin

:CaseAutomation: Automated

:CaseComponent: TemplatesPlugin

:Team: Endeavour

"""

import base64
from time import sleep

from fauxfactory import gen_string
import pytest
import requests

from robottelo.config import settings
from robottelo.constants import (
    FOREMAN_TEMPLATE_IMPORT_URL,
    FOREMAN_TEMPLATE_TEST_TEMPLATE,
)

git = settings.git


class TestTemplateSyncTestCase:
    @pytest.fixture(scope='module', autouse=True)
    def setUpClass(self, module_target_sat):
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

    def test_positive_import_force_locked_template(
        self, module_org, create_import_export_local_dir, target_sat
    ):
        """Assure locked templates are updated from repository when `force` is
        specified.

        :id: b80fbfc4-bcab-4a5d-b6c1-0e22906cd8ab

        :steps:
            1. Import some of the locked template specifying the `force`
               parameter `false`.
            2. After ensuring the template is not updated, Import same locked template
               specifying the `force` parameter `true`.

        :expectedresults:
            1. Assert result is {'message': 'success'}
            2. With force - false, assert that locked template is not updated.
            3. With force - true, assert that the locked template is updated.

        :CaseImportance: Medium
        """
        prefix = gen_string('alpha')
        _, dir_path = create_import_export_local_dir
        target_sat.cli.TemplateSync.imports(
            {'repo': dir_path, 'prefix': prefix, 'organization-ids': module_org.id, 'lock': 'true'}
        )
        ptemplate = target_sat.api.ProvisioningTemplate().search(
            query={'per_page': 10, 'search': f'name~{prefix}', 'organization_id': module_org.id}
        )
        if ptemplate:
            assert ptemplate[0].read().locked
            update_txt = 'updated a little'
            target_sat.execute(f"echo {update_txt} >> {dir_path}/example_template.erb")
            target_sat.cli.TemplateSync.imports(
                {'repo': dir_path, 'prefix': prefix, 'organization-id': module_org.id}
            )
            assert update_txt not in target_sat.cli.Template.dump(
                {'name': f'{prefix}example template'}
            )
            target_sat.cli.TemplateSync.imports(
                {
                    'repo': dir_path,
                    'prefix': prefix,
                    'organization-id': module_org.id,
                    'force': 'true',
                }
            )
            assert update_txt in target_sat.cli.Template.dump({'name': f'{prefix}example template'})
        else:
            pytest.fail('The template is not imported for force test')

    @pytest.mark.skip_if_not_set('git')
    # TODO: add Github ssh key setup for ssh version of this test
    @pytest.mark.parametrize(
        ('url', 'use_proxy_global', 'setup_http_proxy_global'),
        [
            (
                'https://github.com/theforeman/community-templates.git',
                True,
                True,
            ),
            (
                'https://github.com/theforeman/community-templates.git',
                True,
                False,
            ),
            (
                'https://github.com/theforeman/community-templates.git',
                False,
                True,
            ),
        ],
        ids=[
            'use_proxy_global-auth_http_proxy_global-http',
            'use_proxy_global-unauth_http_proxy_global-http',
            'do_not_use_proxy_global-auth_http_proxy_global-http',
        ],
        indirect=[
            'setup_http_proxy_global',
        ],
    )
    def test_positive_import_dir_filtered(
        self,
        module_org,
        create_import_export_local_dir,
        target_sat,
        use_proxy_global,
        setup_http_proxy_global,
        url,
    ):
        """Import a template from git, specifying directory and filter

        :id: 17bfb25a-e215-4f57-b861-294cd018bcf1

        :setup:
            1. Unlock and remove a template to be imported

        :steps:
            1. Import a template, specifying its dir and filter

        :expectedresults:
            1. The template is present

        :CaseImportance: Medium
        """
        proxy, _ = setup_http_proxy_global
        pt_name = 'FreeBSD default fake'
        if target_sat.cli.PartitionTable.list({'search': f'name=\\"{pt_name}\\"'}):
            target_sat.cli.PartitionTable.update({'name': pt_name, 'locked': 0})
            target_sat.cli.PartitionTable.delete({'name': pt_name})
        try:
            data = {
                'repo': url,
                'organization-ids': module_org.id,
                'branch': 'develop',
                'dirname': '/partition_tables_templates/',
                'filter': pt_name,
            }
            if use_proxy_global:
                proxy_hostname = (
                    proxy.split('/')[2].split(':')[0]
                    if '@' not in proxy
                    else proxy.split('@')[1].split(':')[0]
                )
                old_log = target_sat.cutoff_host_setup_log(proxy_hostname, settings.git.hostname)
                data['http-proxy-policy'] = 'global'
            target_sat.cli.TemplateSync.imports(data)
        finally:
            if use_proxy_global:
                target_sat.restore_host_check_log(proxy_hostname, settings.git.hostname, old_log)
        # assert that template has been synced -> is present on the Satellite
        pt = target_sat.cli.PartitionTable.list({'search': f'name=\\"{pt_name}\\"'})
        assert len(pt) == 1
        assert pt_name == pt[0]['name']

    @pytest.mark.e2e
    @pytest.mark.skip_if_not_set('git')
    @pytest.mark.parametrize(
        'url',
        [
            f'http://{git.username}:{git.password}@{git.hostname}:{git.http_port}',
            f'ssh://git@{git.hostname}:{git.ssh_port}',
        ],
        ids=['http', 'ssh'],
    )
    @pytest.mark.parametrize(
        'git_repository',
        [True],
        indirect=True,
        ids=['non_empty_repo'],
    )
    def test_positive_update_templates_in_git(
        self, module_org, git_repository, git_branch, url, module_target_sat
    ):
        """Assure only templates with a given filter are pushed to
        git repository and existing template file is updated.

        :id: 5b0be026-2983-4570-bc63-d9aba36fca65

        :steps:
            1. Repository contains file with same name as exported template.
            2. Export "Atomic Kickstart default" templates to git repo.

        :expectedresults:
            1. Assert matching templates are exported to git repo.
            2. Assert file is updated

        :CaseImportance: High

        :parametrized: yes

        :BZ: 1785613
        """
        dirname = 'export'
        path = f'{dirname}/provisioning_templates/provision/atomic_kickstart_default.erb'
        content = base64.b64encode(gen_string('alpha').encode('ascii'))
        # create template file in repository
        auth = (git.username, git.password)
        api_url = f'http://{git.hostname}:{git.http_port}'
        api_url = f'{api_url}/api/v1/repos/{git.username}/{git_repository["name"]}/contents'
        res = requests.post(
            f'{api_url}/{path}', auth=auth, json={'branch': git_branch, 'content': content}
        )
        assert res.status_code == 201
        url = f'{url}/{git.username}/{git_repository["name"]}'
        output = module_target_sat.cli.TemplateSync.exports(
            {
                'repo': url,
                'branch': git_branch,
                'organization-id': module_org.id,
                'filter': 'User - Registered Users',
                'dirname': dirname,
            }
        ).split('\n')
        exported_count = ['Exported: true' in row.strip() for row in output].count(True)
        assert exported_count == 1
        auth = (git.username, git.password)
        git_file = requests.get(f'{api_url}/{path}', auth=auth, params={'ref': git_branch}).json()
        decoded = base64.b64decode(git_file['content'])
        assert content != decoded

    @pytest.mark.skip_if_not_set('git')
    @pytest.mark.parametrize(
        'url',
        [
            f'http://{git.username}:{git.password}@{git.hostname}:{git.http_port}',
            f'ssh://git@{git.hostname}:{git.ssh_port}',
        ],
        ids=['http', 'ssh'],
    )
    @pytest.mark.parametrize(
        'git_repository',
        [True, False],
        indirect=True,
        ids=['non_empty_repo', 'empty_repo'],
    )
    def test_positive_export_filtered_templates_to_git(
        self, module_org, git_repository, git_branch, url, module_target_sat
    ):
        """Assure only templates with a given filter regex are pushed to
        git repository.

        :id: fd583f85-f170-4b93-b9b1-36d72f31c31f

        :steps:
            1. Export only the templates matching with regex e.g: `^atomic.*` to git repo.

        :expectedresults:
            1. Assert matching templates are exported to git repo.

        :CaseImportance: Critical

        :parametrized: yes

        :BZ: 1785613
        """
        dirname = 'export'
        url = f'{url}/{git.username}/{git_repository["name"]}'
        output = module_target_sat.cli.TemplateSync.exports(
            {
                'repo': url,
                'branch': git_branch,
                'organization-id': module_org.id,
                'filter': 'provisioning',
                'dirname': dirname,
            }
        ).split('\n')
        exported_count = ['Exported: true' in row.strip() for row in output].count(True)
        assert exported_count > 0, 'No templates exported'
        path = f'{dirname}/provisioning_templates/snippet'
        auth = (git.username, git.password)
        api_url = f'http://{git.hostname}:{git.http_port}'
        api_url = f'{api_url}/api/v1/repos/{git.username}/{git_repository["name"]}/contents'
        sleep(10)
        response = requests.get(f'{api_url}/{path}', auth=auth, params={'ref': git_branch})
        response.raise_for_status()
        git_count = len(response.json())
        assert exported_count == git_count, f'Unexpected response: {response.json()}'

    def test_positive_export_filtered_templates_to_temp_dir(self, module_org, target_sat):
        """Assure templates can be exported to /tmp directory without right permissions

        :id: e0427ee8-698e-4868-952f-5f4723ccee87

        :bz: 1778177

        :steps: Export the templates matching with regex e.g: `ansible` to /tmp directory.

        :expectedresults: The templates are exported /tmp directory

        :CaseImportance: Medium
        """
        dir_path = '/tmp'
        output = target_sat.cli.TemplateSync.exports(
            {'repo': dir_path, 'organization-id': module_org.id, 'filter': 'ansible'}
        ).split('\n')
        exported_count = [row == 'Exported: true' for row in output].count(True)
        assert exported_count == int(
            target_sat.execute(f'find {dir_path} -type f -name *ansible* | wc -l').stdout.strip()
        )
