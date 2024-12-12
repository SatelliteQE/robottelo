"""Test class for Foreman Templates Import Export UI

:Requirement: TemplatesPlugin

:CaseAutomation: Automated

:CaseComponent: TemplatesPlugin

:Team: Endeavour

"""

from fauxfactory import gen_string
import pytest
import requests

from robottelo.config import settings
from robottelo.constants import FOREMAN_TEMPLATE_IMPORT_URL, FOREMAN_TEMPLATE_ROOT_DIR


@pytest.fixture(scope='module')
def templates_org(module_target_sat):
    return module_target_sat.api.Organization().create()


@pytest.fixture(scope='module')
def templates_loc(templates_org, module_target_sat):
    return module_target_sat.api.Location(organization=[templates_org]).create()


git = settings.git


@pytest.mark.skip_if_not_set('git')
@pytest.mark.parametrize(
    'setup_http_proxy_without_global_settings',
    [True, False],
    indirect=True,
    ids=['auth_http_proxy', 'unauth_http_proxy'],
)
@pytest.mark.parametrize(
    'use_proxy',
    [True, False],
    ids=['use_proxy', 'do_not_use_proxy'],
)
@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_import_templates(
    session,
    templates_org,
    templates_loc,
    use_proxy,
    setup_http_proxy_without_global_settings,
    target_sat,
):
    """Import template(s) from external source to satellite

    :id: 524bf384-703f-48a5-95ff-7c1cf97db694

    :bz: 1778181, 1778139

    :steps:

        1. Navigate to Host -> Sync Templates, and choose Import.
        2. Select fields:
            associate = always
            filter = Alterator default PXELinux
            prefix = <any_prefix>
            repo = custom Repo
            dirname = provisioning_templates
        3. Submit to Import the template from custom repo.

    :expectedresults:

        1. The reports are displayed for templates imported / not imported.
        2. The filter provisioning template is imported and assigned to current taxonomies

    :CaseImportance: Critical
    """
    proxy, param = setup_http_proxy_without_global_settings
    if not use_proxy and not param:
        # only do-not-use one kind of proxy
        pytest.skip(
            "Invalid parameter combination. DO NOT USE PROXY scenario should only be tested once."
        )
    import_template = 'Alterator default PXELinux'
    branch = 'automation'
    prefix_name = gen_string('alpha', 8)
    # put the http proxy in the correct org and loc
    target_sat.cli.HttpProxy.update(
        {'id': proxy.id, 'organization-ids': [templates_org.id], 'location-ids': [templates_loc.id]}
    )
    try:
        data = {
            'sync_type': 'Import',
            'template.associate': 'Always',
            'template.branch': branch,
            'template.dirname': 'provisioning_templates',
            'template.filter': import_template,
            'template.lock': 'Lock',
            'template.prefix': f'{prefix_name} ',
            'template.repo': FOREMAN_TEMPLATE_IMPORT_URL,
        }
        if use_proxy:
            proxy_hostname = proxy.url.split('/')[2].split(':')[0]
            old_log = target_sat.cutoff_host_setup_log(proxy_hostname, settings.git.hostname)
            data['template.http_proxy_policy'] = 'Custom HTTP proxy'
            data['template.http_proxy_id'] = proxy.name
        with session:
            session.organization.select(org_name=templates_org.name)
            session.location.select(loc_name=templates_loc.name)
            import_title = session.sync_template.sync(data)
            assert import_title == f'Import from {FOREMAN_TEMPLATE_IMPORT_URL} and branch {branch}'
            imported_template = f'{prefix_name} {import_template}'
            assert session.provisioningtemplate.is_locked(imported_template)
            pt = session.provisioningtemplate.read(imported_template)
    finally:
        if use_proxy:
            target_sat.restore_host_check_log(proxy_hostname, settings.git.hostname, old_log)
    assert pt['template']['name'] == imported_template
    assert pt['template']['default'] is False
    assert pt['type']['snippet'] is False
    assert pt['locations']['resources']['assigned'][0] == templates_loc.name
    assert pt['organizations']['resources']['assigned'][0] == templates_org.name
    assert f'name: {import_template}' in pt['template']['template_editor']['editor']


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_export_templates(session, create_import_export_local_dir, target_sat):
    """Export the satellite templates to local directory

    :id: 1c24cf51-7198-48aa-a70a-8c0441333374

    :bz: 1778139

    :steps:

        1. Navigate to Host -> Sync Templates, and choose Export.
        2. Select fields:
            metadata_export_mode = keep
            filter = Kickstart default PXELinux
            repo = `FOREMAN_TEMPLATE_ROOT_DIR`
            dirname = `dir_name`
        3. Submit to Export the template to local directory.

    :expectedresults:

        1. The reports are displayed for templates exported / not exported.
        2. The filter provisioning template is exported in local given directory
        3. The contents in exported files are intact

    :CaseImportance: Critical
    """
    dir_name, dir_path = create_import_export_local_dir
    export_template = 'Kickstart default PXELinux'
    with session:
        export_title = session.sync_template.sync(
            {
                'sync_type': 'Export',
                'template.metadata_export_mode': 'Keep',
                'template.filter': export_template,
                'template.repo': FOREMAN_TEMPLATE_ROOT_DIR,
                'template.dirname': dir_name,
            }
        )
        assert export_title == f'Export to {FOREMAN_TEMPLATE_ROOT_DIR} as user {session._user}'
    exported_file = f'{dir_path}/provisioning_templates/PXELinux/kickstart_default_pxelinux.erb'
    result = target_sat.execute(f'find {exported_file} -type f')
    assert result.status == 0
    search_string = f'name: {export_template}'
    result = target_sat.execute(f"grep -F '{search_string}' {exported_file}")
    assert result.status == 0


@pytest.mark.tier2
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
def test_positive_export_filtered_templates_to_git(session, git_repository, git_branch, url):
    """Assure only templates with a given filter regex are pushed to
    git repository.

    :id: e4de338a-9ab9-492e-ac42-6cc2ebcd1792

    :steps:
        1. Export only the templates matching with regex e.g: `^atomic.*` to git repo.

    :expectedresults:
        1. Assert matching templates are exported to git repo.

    :BZ: 1785613, 2013759

    :parametrized: yes

    :CaseImportance: Critical
    """
    url = f'{url}/{git.username}/{git_repository["name"]}'
    dirname = 'export'
    with session:
        export_title = session.sync_template.sync(
            {
                'sync_type': 'Export',
                'template.metadata_export_mode': 'Keep',
                'template.filter': 'atomic',
                'template.repo': url,
                'template.branch': git_branch,
                'template.dirname': dirname,
            }
        )
        assert (
            export_title == f'Export to {url.replace(git.password, "*****")} '
            f'and branch {git_branch} as user {session._user}'
        )
        path = f"{dirname}/provisioning_templates/provision"
        auth = (git.username, git.password)
        api_url = f"http://{git.hostname}:{git.http_port}/api/v1/repos/{git.username}"
        git_count = requests.get(
            f'{api_url}/{git_repository["name"]}/contents/{path}',
            auth=auth,
            params={"ref": git_branch},
        ).json()
        assert len(git_count) == 1
