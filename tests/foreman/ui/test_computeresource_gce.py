"""Test for Compute Resource UI

:Requirement: ComputeResources GCE

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: ComputeResources-GCE

:Assignee: lvrtelov

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_string
from nailgun import entities

from robottelo.constants import COMPUTE_PROFILE_SMALL
from robottelo.constants import FOREMAN_PROVIDERS
from robottelo.constants import GCE_EXTERNAL_IP_DEFAULT
from robottelo.constants import GCE_MACHINE_TYPE_DEFAULT
from robottelo.constants import GCE_NETWORK_DEFAULT
from robottelo.helpers import download_gce_cert
from robottelo.test import settings


@pytest.mark.tier2
@pytest.mark.upgrade
@pytest.mark.skip_if_not_set('http_proxy', 'gce')
def test_positive_default_end_to_end_with_custom_profile(
    session, module_org, module_loc, module_gce_settings
):
    """Create GCE compute resource with default properties and apply it's basic functionality.

    :id: 59ffd83e-a984-4c22-b91b-cad055b4fbd7

    :Steps:

        1. Create an GCE compute resource with default properties.
        2. Update the compute resource name and add new taxonomies.
        3. Associate compute profile with custom properties to GCE compute resource
        4. Delete the compute resource.

    :expectedresults: The GCE compute resource is created, updated, compute profile associated and
        deleted.

    :CaseLevel: Integration

    :CaseImportance: Critical
    """
    cr_name = gen_string('alpha')
    new_cr_name = gen_string('alpha')
    cr_description = gen_string('alpha')
    new_org = entities.Organization().create()
    new_loc = entities.Location().create()
    download_gce_cert()
    http_proxy = entities.HTTPProxy(
        name=gen_string('alpha', 15),
        url=settings.http_proxy.auth_proxy_url,
        username=settings.http_proxy.username,
        password=settings.http_proxy.password,
        organization=[module_org.id],
        location=[module_loc.id],
    ).create()
    with session:
        # Compute Resource Create and Assertions
        session.computeresource.create(
            {
                'name': cr_name,
                'description': cr_description,
                'provider': FOREMAN_PROVIDERS['google'],
                'provider_content.http_proxy.value': http_proxy.name,
                'provider_content.google_project_id': settings.gce.project_id,
                'provider_content.client_email': settings.gce.client_email,
                'provider_content.certificate_path': settings.gce.cert_path,
                'provider_content.zone.value': settings.gce.zone,
                'organizations.resources.assigned': [module_org.name],
                'locations.resources.assigned': [module_loc.name],
            }
        )
        cr_values = session.computeresource.read(cr_name)
        assert cr_values['name'] == cr_name
        assert cr_values['provider_content']['zone']['value']
        assert cr_values['provider_content']['http_proxy']['value'] == http_proxy.name
        assert cr_values['organizations']['resources']['assigned'] == [module_org.name]
        assert cr_values['locations']['resources']['assigned'] == [module_loc.name]
        assert cr_values['provider_content']['google_project_id'] == settings.gce.project_id
        assert cr_values['provider_content']['client_email'] == settings.gce.client_email
        # Compute Resource Edit/Updates and Assertions
        session.computeresource.edit(
            cr_name,
            {
                'name': new_cr_name,
                'organizations.resources.assigned': [new_org.name],
                'locations.resources.assigned': [new_loc.name],
            },
        )
        assert not session.computeresource.search(cr_name)
        cr_values = session.computeresource.read(new_cr_name)
        assert cr_values['name'] == new_cr_name
        assert set(cr_values['organizations']['resources']['assigned']) == {
            module_org.name,
            new_org.name,
        }
        assert set(cr_values['locations']['resources']['assigned']) == {
            module_loc.name,
            new_loc.name,
        }

        # Compute Profile edit/updates and Assertions
        session.computeresource.update_computeprofile(
            new_cr_name,
            COMPUTE_PROFILE_SMALL,
            {
                'provider_content.machine_type': GCE_MACHINE_TYPE_DEFAULT,
                'provider_content.network': GCE_NETWORK_DEFAULT,
                'provider_content.external_ip': GCE_EXTERNAL_IP_DEFAULT,
                'provider_content.default_disk_size': '15',
            },
        )
        cr_profile_values = session.computeresource.read_computeprofile(
            new_cr_name, COMPUTE_PROFILE_SMALL
        )
        assert cr_profile_values['breadcrumb'] == f'Edit {COMPUTE_PROFILE_SMALL}'
        assert cr_profile_values['compute_profile'] == COMPUTE_PROFILE_SMALL
        assert (
            cr_profile_values['compute_resource']
            == f'{new_cr_name} ({settings.gce.zone}-{FOREMAN_PROVIDERS["google"]})'
        )
        assert cr_profile_values['provider_content']['machine_type'] == GCE_MACHINE_TYPE_DEFAULT
        assert cr_profile_values['provider_content']['network'] == GCE_NETWORK_DEFAULT

        assert cr_profile_values['provider_content']['external_ip'] == GCE_EXTERNAL_IP_DEFAULT

        assert cr_profile_values['provider_content']['default_disk_size'] == '15'

        # Compute Resource Delete and Assertion
        session.computeresource.delete(new_cr_name)
        assert not session.computeresource.search(new_cr_name)
