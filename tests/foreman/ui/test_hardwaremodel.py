"""Test class for Hardware Model UI

:Requirement: HardwareModel

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: Low

:Upstream: No
"""
from fauxfactory import gen_string
from nailgun import entities
from pytest import raises

from robottelo.decorators import tier2, upgrade
from robottelo.ui.utils import create_fake_host


@tier2
@upgrade
def test_positive_end_to_end(session, module_org, module_loc):
    """Perform end to end testing for hardware model component

    :id: 93663cc9-7c8f-4f43-8050-444be1313bed

    :expectedresults: All expected CRUD actions finished successfully

    :CaseLevel: Integration

    :CaseImportance: High
    """
    name = gen_string('alpha')
    model = gen_string('alphanumeric')
    vendor_class = gen_string('alpha')
    info = gen_string('alpha')
    new_name = gen_string('alpha')
    host_template = entities.Host(organization=module_org, location=module_loc)
    host_template.create_missing()
    with session:
        # Create new hardware model
        session.hardwaremodel.create({
            'name': name,
            'hardware_model': model,
            'vendor_class': vendor_class,
            'info': info,
        })
        assert session.hardwaremodel.search(name)[0]['Name'] == name
        hm_values = session.hardwaremodel.read(name)
        assert hm_values['name'] == name
        assert hm_values['hardware_model'] == model
        assert hm_values['vendor_class'] == vendor_class
        assert hm_values['info'] == info
        # Create host with associated hardware model
        host_name = create_fake_host(
            session,
            host_template,
            extra_values={'additional_information.hardware_model': name}
        )
        host_values = session.host.read(host_name, 'additional_information')
        assert host_values['additional_information']['hardware_model'] == name
        # Update hardware model with new name
        session.hardwaremodel.update(name, {'name': new_name})
        assert session.hardwaremodel.search(new_name)[0]['Name'] == new_name
        host_values = session.host.read(host_name, 'additional_information')
        assert host_values['additional_information']['hardware_model'] == new_name
        # Make an attempt to delete hardware model that associated with host
        with raises(AssertionError) as context:
            session.hardwaremodel.delete(new_name)
        assert "error: '{} is used by {}'".format(
            new_name, host_name) in str(context.value)
        session.host.update(host_name, {'additional_information.hardware_model': ''})
        # Delete hardware model
        session.hardwaremodel.delete(new_name)
        assert not session.hardwaremodel.search(new_name)
