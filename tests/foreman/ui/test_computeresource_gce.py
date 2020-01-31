"""Test for Compute Resource UI

:Requirement: ComputeResources GCE

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: ComputeResources-GCE

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_string
from nailgun import entities
from pytest import skip
from robottelo.constants import (
    COMPUTE_PROFILE_SMALL,
    FOREMAN_PROVIDERS,
    GCE_EXTERNAL_IP_DEFAULT,
    GCE_MACHINE_TYPE_DEFAULT,
    GCE_NETWORK_DEFAULT
)
from robottelo.decorators import setting_is_set, tier2, upgrade
from robottelo.helpers import download_gce_cert
from robottelo.test import settings

if not setting_is_set('gce'):
    skip('skipping tests due to missing gce settings', allow_module_level=True)

GCE_SETTINGS = dict(
    project_id=settings.gce.project_id,
    client_email=settings.gce.client_email,
    cert_path=settings.gce.cert_path,
    zone=settings.gce.zone,
    cert_url=settings.gce.cert_url,
)


@tier2
@upgrade
def test_positive_default_end_to_end_with_custom_profile(session):
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
    org = entities.Organization().create()
    loc = entities.Location().create()
    new_org = entities.Organization().create()
    new_loc = entities.Location().create()
    download_gce_cert(
        GCE_SETTINGS['cert_url'], GCE_SETTINGS['cert_path'])

    with session:
        session.organization.select(org_name=org.name)
        session.location.select(loc_name=loc.name)
        # Compute Resource Create and Assertions
        session.computeresource.create({
            'name': cr_name,
            'description': cr_description,
            'provider': FOREMAN_PROVIDERS['google'],
            'provider_content.google_project_id': GCE_SETTINGS['project_id'],
            'provider_content.client_email': GCE_SETTINGS['client_email'],
            'provider_content.certificate_path': GCE_SETTINGS['cert_path'],
            'provider_content.zone.value': GCE_SETTINGS['zone'],
            'organizations.resources.assigned': [org.name],
            'locations.resources.assigned': [loc.name]
        })
        cr_values = session.computeresource.read(cr_name)
        assert cr_values['name'] == cr_name
        assert cr_values['provider_content']['zone']['value']
        assert (cr_values['organizations']['resources']['assigned']
                == [org.name])
        assert (cr_values['locations']['resources']['assigned']
                == [loc.name])
        assert cr_values['provider_content']['google_project_id'] == GCE_SETTINGS[
            'project_id']
        assert cr_values['provider_content']['client_email'] == GCE_SETTINGS[
            'client_email']
        # Compute Resource Edit/Updates and Assertions
        session.computeresource.edit(cr_name, {
            'name': new_cr_name,
            'organizations.resources.assigned': [new_org.name],
            'locations.resources.assigned': [new_loc.name],
        })
        assert not session.computeresource.search(cr_name)
        cr_values = session.computeresource.read(new_cr_name)
        assert cr_values['name'] == new_cr_name
        assert set(
            cr_values['organizations']['resources']['assigned']) == {org.name, new_org.name}
        assert set(
            cr_values['locations']['resources']['assigned']) == {loc.name, new_loc.name}

        # Compute Profile edit/updates and Assertions
        session.computeresource.update_computeprofile(
            new_cr_name,
            COMPUTE_PROFILE_SMALL,
            {
                'provider_content.machine_type': GCE_MACHINE_TYPE_DEFAULT,
                'provider_content.network': GCE_NETWORK_DEFAULT,
                'provider_content.external_ip': GCE_EXTERNAL_IP_DEFAULT,
                'provider_content.default_disk_size': '15'
            }
        )
        cr_profile_values = session.computeresource.read_computeprofile(
            new_cr_name, COMPUTE_PROFILE_SMALL)
        assert cr_profile_values['breadcrumb'] == 'Edit {0}'.format(COMPUTE_PROFILE_SMALL)
        assert cr_profile_values['compute_profile'] == COMPUTE_PROFILE_SMALL
        assert cr_profile_values['compute_resource'] == '{0} ({1}-{2})'.format(
            new_cr_name, GCE_SETTINGS['zone'], FOREMAN_PROVIDERS['google'])
        assert (cr_profile_values['provider_content']['machine_type']
                == GCE_MACHINE_TYPE_DEFAULT)
        assert cr_profile_values['provider_content']['network'] == GCE_NETWORK_DEFAULT

        assert cr_profile_values['provider_content']['external_ip'] == GCE_EXTERNAL_IP_DEFAULT

        assert cr_profile_values['provider_content']['default_disk_size'] == '15'

        # Compute Resource Delete and Assertion
        session.computeresource.delete(new_cr_name)
        assert not session.computeresource.search(new_cr_name)
