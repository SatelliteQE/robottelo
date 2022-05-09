"""Unit tests for the ``provisioning_templates`` paths.

A full API reference is available here:
http://theforeman.org/api/apidoc/v2/provisioning_templates.html

:Requirement: Template

:CaseAutomation: Automated

:CaseComponent: ProvisioningTemplates

:Assignee: ogajduse

:TestType: Functional

:CaseLevel: Integration

:CaseImportance: High

:Upstream: No
"""
from random import choice

import pytest
from fauxfactory import gen_choice
from fauxfactory import gen_string
from nailgun import client
from nailgun import entities
from requests.exceptions import HTTPError

from robottelo.config import get_credentials
from robottelo.config import settings
from robottelo.datafactory import invalid_names_list
from robottelo.datafactory import valid_data_list
from robottelo.helpers import get_nailgun_config


@pytest.fixture(scope="module")
def module_location(module_location):
    yield module_location
    module_location.delete()


@pytest.fixture(scope="module")
def module_org(module_org):
    yield module_org
    module_org.delete()


@pytest.fixture(scope="module")
def module_user(module_org, module_location):
    """Creates an org admin role and user"""
    user_login = gen_string('alpha')
    user_password = gen_string('alpha')
    # Create user with Manager role
    orig_role = entities.Role().search(query={'search': 'name="Organization admin"'})[0]
    new_role_dict = entities.Role(id=orig_role.id).clone(
        data={
            'role': {
                'name': f"test_template_admin_{gen_string('alphanumeric', 3)}",
                'organization_ids': [module_org.id],
                'location_ids': [module_location.id],
            }
        }
    )
    new_role = entities.Role(id=new_role_dict['id']).read()
    user = entities.User(
        role=[new_role],
        admin=False,
        login=user_login,
        password=user_password,
        organization=[module_org],
        location=[module_location],
    ).create()
    yield (user, user_login, user_password)
    user.delete()
    new_role.delete()


@pytest.fixture(scope="function")
def tftpboot(module_org, target_sat):
    """This fixture removes the current deployed templates from TFTP, and sets up new ones.
    It manipulates the global defaults, so it shouldn't be used in concurrent environment

    :param module_org:
    :return: A dictionary containing nailgun entities, names, values and paths of the custom
    Templates
    """
    tftpboot_path = '/var/lib/tftpboot'
    default_templates = {
        'pxegrub': {
            'setting': 'global_PXEGrub',
            'path': f'{tftpboot_path}/grub/menu.lst',
            'kind': 'PXEGrub',
        },
        'pxegrub2': {
            'setting': 'global_PXEGrub2',
            'path': f'{tftpboot_path}/grub2/grub.cfg',
            'kind': 'PXEGrub2',
        },
        'pxelinux': {
            'setting': 'global_PXELinux',
            'path': f'{tftpboot_path}/pxelinux.cfg/default',
            'kind': 'PXELinux',
        },
        'ipxe': {
            'setting': 'global_iPXE',
            'path': f'{target_sat.url}/unattended/iPXE?bootstrap=1',
            'kind': 'iPXE',
        },
    }
    # we keep the value of these for the teardown
    default_settings = entities.Setting().search(query={"search": "name ~ Global default"})
    kinds = entities.TemplateKind().search(query={"search": "name ~ PXE"})

    # clean the already-deployed default pxe configs
    target_sat.execute('rm {}'.format(' '.join([i['path'] for i in default_templates.values()])))

    # create custom Templates per kind
    for template in default_templates.values():
        template['entity'] = entities.ProvisioningTemplate(
            name=gen_string('alpha'),
            organization=[module_org],
            snippet=False,
            template_kind=[i.id for i in kinds if i.name == template['kind']][0],
            template=f"<%= foreman_server_url %> {template['kind']}",
        ).create(create_missing=False)

        # Update the global settings to use newly created template
        template['setting_id'] = entities.Setting(
            id=[i.id for i in default_settings if i.name == template['setting']][0],
            value=template['entity'].name,
        ).update(fields=['value'])

    yield default_templates

    # delete the deployed tftp files
    target_sat.execute('rm {}'.format(' '.join([i['path'] for i in default_templates.values()])))
    # set the settings back to defaults
    for setting in default_settings:
        if setting.value is None:
            setting.value = ''
        setting.update(fields=['value'] or '')


class TestProvisioningTemplate:
    """Tests for provisioning templates

    :CaseLevel: Acceptance
    """

    @pytest.mark.tier1
    @pytest.mark.upgrade
    def test_positive_end_to_end_crud(self, module_org, module_location, module_user):
        """Create a new provisioning template with several attributes, update them,
        clone the provisioning template and then delete it

        :id: 8dfbb234-7a52-4873-be72-4de086472670

        :expectedresults: Template is created, with all the given attributes, updated, cloned and
                          deleted

        :CaseImportance: Critical
        """
        cfg = get_nailgun_config()
        cfg.auth = (module_user[1], module_user[2])
        name = gen_string('alpha')
        new_name = gen_string('alpha')
        template_kind = choice(entities.TemplateKind().search())

        template = entities.ProvisioningTemplate(
            name=name,
            organization=[module_org],
            location=[module_location],
            snippet=False,
            template_kind=template_kind,
        ).create()
        assert template.name == name
        assert len(template.organization) == 1, "Template should be assigned to a single org here"
        assert template.organization[0].id == module_org.id
        assert len(template.location) == 1, "Template should be assigned to a single location here"
        assert template.location[0].id == module_location.id
        assert template.snippet is False, "Template snippet attribute is True instead of False"
        assert template.template_kind.id == template_kind.id

        # negative create
        with pytest.raises(HTTPError) as e1:
            entities.ProvisioningTemplate(name=gen_choice(invalid_names_list())).create()
        assert e1.value.response.status_code == 422

        invalid = entities.ProvisioningTemplate(snippet=False)
        invalid.create_missing()
        invalid.template_kind = None
        invalid.template_kind_name = gen_string('alpha')
        with pytest.raises(HTTPError) as e2:
            invalid.create(create_missing=False)
        assert e2.value.response.status_code == 422

        # update
        assert template.template_kind.id == template_kind.id, "Template kind id doesn't match"
        updated = entities.ProvisioningTemplate(cfg, id=template.id, name=new_name).update(['name'])
        assert updated.name == new_name, "The Provisioning template wasn't properly renamed"
        # clone

        template_origin = template.read_json()
        # remove unique keys
        unique_keys = ('updated_at', 'created_at', 'id', 'name')
        template_origin = {
            key: value for key, value in template_origin.items() if key not in unique_keys
        }

        dupe_name = gen_choice(list(valid_data_list().values()))
        dupe_json = entities.ProvisioningTemplate(
            id=template.clone(data={'name': dupe_name})['id']
        ).read_json()
        dupe_template = entities.ProvisioningTemplate(id=dupe_json['id'])
        dupe_json = {key: value for key, value in dupe_json.items() if key not in unique_keys}
        assert template_origin == dupe_json

        # delete
        dupe_template.delete()
        template.delete()
        with pytest.raises(HTTPError) as e3:
            updated.read()
        assert e3.value.response.status_code == 404

    @pytest.mark.tier2
    @pytest.mark.upgrade
    @pytest.mark.run_in_one_thread
    def test_positive_build_pxe_default(self, tftpboot, target_sat):
        """Call the "build_pxe_default" path.

        :id: ca19d9da-1049-4b39-823b-933fc1a0cebd

        :expectedresults: The response is a JSON payload, all templates are deployed to TFTP/HTTP
                          and are rendered correctly

        :CaseLevel: Integration

        :CaseImportance: Critical

        :BZ: 1202564
        """
        response = client.post(
            entities.ProvisioningTemplate().path('build_pxe_default'),
            auth=get_credentials(),
            verify=False,
        )
        response.raise_for_status()
        assert type(response.json()) == dict
        for template in tftpboot.values():
            if template['path'].startswith('http'):
                r = client.get(template['path'], verify=False)
                r.raise_for_status()
                rendered = r.text
            else:
                rendered = target_sat.execute(f'cat {template["path"]}').stdout.splitlines()[0]
            assert (
                rendered == f"{settings.server.scheme}://"
                f"{target_sat.hostname} {template['kind']}"
            )
