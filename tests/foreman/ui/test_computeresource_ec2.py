"""Test for Compute Resource UI

:Requirement: Computeresource RHV

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_string
from nailgun import entities
from pytest import skip

from robottelo.config import settings
from robottelo.constants import (
    AWS_EC2_FLAVOR_T2_MICRO,
    COMPUTE_PROFILE_LARGE,
    DEFAULT_LOC,
    EC2_REGION_CA_CENTRAL_1,
    FOREMAN_PROVIDERS
)
from robottelo.decorators import fixture, setting_is_set, tier2


if not setting_is_set('ec2'):
    skip('skipping tests due to missing ec2 settings', allow_module_level=True)


@fixture(scope='module')
def module_org():
    return entities.Organization().create()


@fixture(scope='module')
def module_loc():
    default_loc_id = entities.Location().search(
        query={'search': 'name="{}"'.format(DEFAULT_LOC)})[0].id
    return entities.Location(id=default_loc_id).read()


@fixture(scope='module')
def module_ec2_settings():
    return dict(
        access_key=settings.ec2.access_key,
        secret_key=settings.ec2.secret_key,
        region=settings.ec2.region,
        image=settings.ec2.image,
        availability_zone=settings.ec2.availability_zone,
        subnet=settings.ec2.subnet,
        security_groups=settings.ec2.security_groups,
        managed_ip=settings.ec2.managed_ip,
    )


@tier2
def test_positive_default_end_to_end_with_custom_profile(
        session, module_org, module_loc, module_ec2_settings):
    """Create EC2 compute resource with default properties and apply it's basic functionality.

    :id: 33f80a8f-2ecf-4f15-b0c3-aab5fe0ac8d3

    :Steps:

        1. Create an EC2 compute resource with default properties and taxonomies.
        2. Update the compute resource name and add new taxonomies.
        3. Associate compute profile with custom properties to ec2 compute resource
        4. Delete the compute resource.

    :expectedresults: The EC2 compute resource is created, updated, compute profile associated and
        deleted.

    :CaseLevel: Integration

    :BZ: 1451626

    :CaseImportance: High
    """
    cr_name = gen_string('alpha')
    new_cr_name = gen_string('alpha')
    cr_description = gen_string('alpha')
    new_org = entities.Organization().create()
    new_loc = entities.Location().create()
    with session:
        session.computeresource.create({
            'name': cr_name,
            'description': cr_description,
            'provider': FOREMAN_PROVIDERS['ec2'],
            'provider_content.access_key': module_ec2_settings['access_key'],
            'provider_content.secret_key': module_ec2_settings['secret_key'],
            'provider_content.region.value': module_ec2_settings['region'],
            'organizations.resources.assigned': [module_org.name],
            'locations.resources.assigned': [module_loc.name],
        })
        cr_values = session.computeresource.read(cr_name)
        assert cr_values['name'] == cr_name
        assert cr_values['description'] == cr_description
        assert (cr_values['organizations']['resources']['assigned']
                == [module_org.name])
        assert (cr_values['locations']['resources']['assigned']
                == [module_loc.name])
        session.computeresource.edit(cr_name, {
            'name': new_cr_name,
            'organizations.resources.assigned': [new_org.name],
            'locations.resources.assigned': [new_loc.name],
        })
        assert not session.computeresource.search(cr_name)
        cr_values = session.computeresource.read(new_cr_name)
        assert cr_values['name'] == new_cr_name
        assert (set(cr_values['organizations']['resources']['assigned'])
                == {module_org.name, new_org.name})
        assert (set(cr_values['locations']['resources']['assigned'])
                == {module_loc.name, new_loc.name})
        session.computeresource.update_computeprofile(
            new_cr_name,
            COMPUTE_PROFILE_LARGE,
            {
                'provider_content.flavor': AWS_EC2_FLAVOR_T2_MICRO,
                'provider_content.availability_zone': module_ec2_settings['availability_zone'],
                'provider_content.subnet': module_ec2_settings['subnet'],
                'provider_content.security_groups.assigned': module_ec2_settings[
                    'security_groups'],
                'provider_content.managed_ip': module_ec2_settings['managed_ip'],
            }
        )
        cr_profile_values = session.computeresource.read_computeprofile(
            new_cr_name, COMPUTE_PROFILE_LARGE)
        assert cr_profile_values['breadcrumb'] == 'Edit {0}'.format(COMPUTE_PROFILE_LARGE)
        assert cr_profile_values['compute_profile'] == COMPUTE_PROFILE_LARGE
        assert cr_profile_values['compute_resource'] == '{0} ({1}-{2})'.format(
            new_cr_name, module_ec2_settings['region'], FOREMAN_PROVIDERS['ec2'])
        assert (cr_profile_values['provider_content']['managed_ip']
                == module_ec2_settings['managed_ip'])
        assert cr_profile_values['provider_content']['flavor'] == AWS_EC2_FLAVOR_T2_MICRO
        session.computeresource.delete(new_cr_name)
        assert not session.computeresource.search(new_cr_name)


@tier2
def test_positive_create_ec2_with_custom_region(session, module_ec2_settings):
    """Create a new ec2 compute resource with custom region

    :id: aeb0c52e-34dd-4574-af34-a6d8721724a7

    :customerscenario: true

    :expectedresults: An ec2 compute resource is created
        successfully.

    :BZ: 1456942

    :CaseLevel: Integration

    :CaseImportance: Critical
    """
    cr_name = gen_string('alpha')
    with session:
        session.computeresource.create({
            'name': cr_name,
            'provider': FOREMAN_PROVIDERS['ec2'],
            'provider_content.access_key': module_ec2_settings['access_key'],
            'provider_content.secret_key': module_ec2_settings['secret_key'],
            'provider_content.region.value': EC2_REGION_CA_CENTRAL_1
        })
        cr_values = session.computeresource.read(cr_name)
        assert cr_values['name'] == cr_name
