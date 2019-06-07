# -*- encoding: utf-8 -*-
"""Test class for Partition Table UI

:Requirement: Partitiontable

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_string
from nailgun import entities
from pytest import raises

from robottelo.constants import PARTITION_SCRIPT_DATA_FILE
from robottelo.decorators import fixture, tier2, upgrade
from robottelo.helpers import read_data_file


@fixture(scope='module')
def module_org():
    return entities.Organization().create()


@fixture(scope='module')
def module_loc():
    return entities.Location().create()


@fixture(scope='module')
def template_data():
    return read_data_file(PARTITION_SCRIPT_DATA_FILE)


@tier2
def test_positive_create_default_for_organization(session):
    """Create new partition table with enabled 'default' option. Check
    that newly created organization has that partition table assigned to it

    :id: 91c64054-cd0c-4d4b-888b-17d42e298527

    :expectedresults: New partition table is created and is present in the
        list of selected partition tables for any new organization

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    org_name = gen_string('alpha')
    with session:
        session.partitiontable.create({
            'template.name': name,
            'template.default': True,
            'template.template_editor': gen_string('alpha')
        })
        session.organization.create({'name': org_name})
        session.organization.select(org_name)
        assert session.partitiontable.search(name)[0]['Name'] == name


@tier2
def test_positive_create_custom_organization(session):
    """Create new partition table with disabled 'default' option. Check
    that newly created organization does not contain that partition table.

    :id: 69e6df0f-af1f-4aa2-8987-3e3b9a16be37

    :expectedresults: New partition table is created and is not present in
        the list of selected partition tables for any new organization

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    org_name = gen_string('alpha')
    with session:
        session.partitiontable.create({
            'template.name': name,
            'template.default': False,
            'template.template_editor': gen_string('alpha')
        })
        session.organization.create({'name': org_name})
        session.organization.select(org_name)
        assert not session.partitiontable.search(name)


@tier2
def test_positive_create_default_for_location(session):
    """Create new partition table with enabled 'default' option. Check
    that newly created location has that partition table assigned to it

    :id: 8dfaae7c-2f33-4f0d-93f6-1f78ea4d750d

    :expectedresults: New partition table is created and is present in the
        list of selected partition tables for any new location

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    loc_name = gen_string('alpha')
    with session:
        session.partitiontable.create({
            'template.name': name,
            'template.default': True,
            'template.template_editor': gen_string('alpha')
        })
        session.location.create({'name': loc_name})
        session.location.select(loc_name)
        assert session.partitiontable.search(name)[0]['Name'] == name


@tier2
def test_positive_create_custom_location(session):
    """Create new partition table with disabled 'default' option. Check
    that newly created location does not contain that partition table.

    :id: 094d4583-763b-48d4-a89a-23b90741fd6f

    :expectedresults: New partition table is created and is not present in
        the list of selected partition tables for any new location

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    loc_name = gen_string('alpha')
    with session:
        session.partitiontable.create({
            'template.name': name,
            'template.default': False,
            'template.template_editor': gen_string('alpha')
        })
        session.location.create({'name': loc_name})
        session.location.select(loc_name)
        assert not session.partitiontable.search(name)


@tier2
def test_positive_delete_with_lock_and_unlock(session):
    """Create new partition table and lock it, try delete unlock and retry

    :id: a5143f5b-7c8e-4700-a850-01815bb54760

    :expectedresults: New partition table is created and not deleted when
        locked and only deleted after unlock

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    with session:
        session.partitiontable.create({
            'template.name': name,
            'template.default': True,
            'template.template_editor': gen_string('alpha')
        })
        assert session.partitiontable.search(name)[0]['Name'] == name
        session.partitiontable.lock(name)
        with raises(ValueError):
            session.partitiontable.delete(name)
        session.partitiontable.unlock(name)
        session.partitiontable.delete(name)
        assert not session.partitiontable.search(name)


@tier2
def test_positive_clone(session):
    """Create new partition table and clone it

    :id: 6050f66f-82e0-4694-a482-5ea449ed9a9d

    :expectedresults: New partition table is created and cloned successfully

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    audit_comment = gen_string('alpha')
    os_family = 'Red Hat'
    with session:
        session.partitiontable.create({
            'template.name': name,
            'template.template_editor': gen_string('alpha')
        })
        session.partitiontable.clone(
            name,
            {
                'template.name': new_name,
                'template.default': True,
                'template.snippet': False,
                'template.os_family_selection.os_family': os_family,
                'template.audit_comment': audit_comment,
            }
        )
        pt = session.partitiontable.read(new_name)
        assert pt['template']['name'] == new_name
        assert pt['template']['os_family_selection']['os_family'] == os_family


@tier2
@upgrade
def test_positive_end_to_end(session, module_org, module_loc, template_data):
    """Perform end to end testing for partition table component

    :id: ade8e9b8-01a7-476b-ad01-f3e6c119ec25

    :expectedresults: All expected CRUD actions finished successfully

    :CaseLevel: Integration

    :CaseImportance: High
    """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    audit_comment = gen_string('alpha')
    os_family = 'FreeBSD'
    input_name = gen_string('alpha')
    template_inputs = [{
        'name': input_name,
        'required': True,
        'input_type': 'Puppet parameter',
        'input_content.puppet_class_name': gen_string('alpha'),
        'input_content.puppet_parameter_name':  gen_string('alpha'),
        'input_content.description': gen_string('alpha')
    }]
    with session:
        session.partitiontable.create({
            'template.name': name,
            'template.default': True,
            'template.snippet': True,
            'template.template_editor': template_data,
            'template.audit_comment': audit_comment,
            'inputs': template_inputs,
            'organizations.resources.assigned': [module_org.name],
            'locations.resources.assigned': [module_loc.name],
        })
        assert session.partitiontable.search(name)[0]['Name'] == name
        pt = session.partitiontable.read(name)
        assert pt['template']['name'] == name
        assert pt['template']['default'] is True
        assert pt['template']['snippet'] is True
        assert pt['template']['template_editor'] == template_data
        assert pt['inputs'][0]['name'] == input_name
        assert pt['inputs'][0]['required'] is True
        assert pt['inputs'][0]['input_type'] == 'Puppet parameter'
        assert pt['locations']['resources']['assigned'][0] == module_loc.name
        assert pt['organizations']['resources']['assigned'][0] == module_org.name
        session.partitiontable.update(
            name,
            {
                'template.name': new_name,
                'template.snippet': False,
                'template.os_family_selection.os_family': os_family,
            }
        )
        assert session.partitiontable.search(new_name)[0]['Name'] == new_name
        updated_pt = session.partitiontable.read(new_name)
        assert updated_pt['template']['snippet'] is False
        assert updated_pt['template']['os_family_selection']['os_family'] == os_family
        session.partitiontable.delete(new_name)
        assert not session.partitiontable.search(new_name)
