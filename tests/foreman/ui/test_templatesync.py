"""Test class for Foreman Templates Import Export UI

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

from robottelo import ssh
from robottelo.constants import FOREMAN_TEMPLATE_IMPORT_URL
from robottelo.constants import FOREMAN_TEMPLATE_ROOT_DIR


@pytest.fixture(scope='module')
def templates_org():
    return entities.Organization().create()


@pytest.fixture(scope='module')
def templates_loc(templates_org):
    return entities.Location(organization=[templates_org]).create()


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_import_templates(session, templates_org, templates_loc):
    """Import template(s) from external source to satellite

    :id: 524bf384-703f-48a5-95ff-7c1cf97db694

    :bz: 1778181, 1778139

    :Steps:

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
    import_template = 'Alterator default PXELinux'
    branch = 'automation'
    prefix_name = gen_string('alpha', 8)
    with session:
        session.organization.select(org_name=templates_org.name)
        session.location.select(loc_name=templates_loc.name)
        import_title = session.sync_template.sync(
            {
                'sync_type': 'Import',
                'template.associate': 'Always',
                'template.branch': branch,
                'template.dirname': 'provisioning_templates',
                'template.filter': import_template,
                'template.lock': 'Lock',
                'template.prefix': f'{prefix_name} ',
                'template.repo': FOREMAN_TEMPLATE_IMPORT_URL,
            }
        )
        assert import_title == f'Import from {FOREMAN_TEMPLATE_IMPORT_URL} and branch {branch}'
        imported_template = f'{prefix_name} {import_template}'
        assert session.provisioningtemplate.is_locked(imported_template)
        pt = session.provisioningtemplate.read(imported_template)
        assert pt['template']['name'] == imported_template
        assert pt['template']['default'] is False
        assert pt['type']['snippet'] is False
        assert pt['locations']['resources']['assigned'][0] == templates_loc.name
        assert pt['organizations']['resources']['assigned'][0] == templates_org.name
        assert f'name: {import_template}' in pt['template']['template_editor']['editor']


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_export_templates(session, create_import_export_local_dir):
    """Export the satellite templates to local directory

    :id: 1c24cf51-7198-48aa-a70a-8c0441333374

    :bz: 1778139

    :Steps:

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
    result = ssh.command(f'find {exported_file} -type f')
    assert result.return_code == 0
    search_string = f'name: {export_template}'
    result = ssh.command(f"grep -F '{search_string}' {exported_file}")
    assert result.return_code == 0
