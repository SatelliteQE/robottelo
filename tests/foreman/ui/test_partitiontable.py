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
from pytest import raises

from robottelo.constants import PARTITION_SCRIPT_DATA_FILE
from robottelo.decorators import tier2
from robottelo.helpers import get_data_file

PARTITION_SCRIPT_DATA_FILE = get_data_file(PARTITION_SCRIPT_DATA_FILE)


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
            'name': name,
            'default': True,
            'template': PARTITION_SCRIPT_DATA_FILE
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
            'name': name,
            'default': False,
            'template': PARTITION_SCRIPT_DATA_FILE
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
            'name': name,
            'default': True,
            'template': PARTITION_SCRIPT_DATA_FILE
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
            'name': name,
            'default': False,
            'template': PARTITION_SCRIPT_DATA_FILE
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
    audit_comment = gen_string('alpha')
    with session:
        session.partitiontable.create({
            'name': name,
            'default': True,
            'snippet': True,
            'audit_comment': audit_comment,
            'template': PARTITION_SCRIPT_DATA_FILE
        }, )
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
    os_family_selection = {'os_family': 'Red Hat'}
    with session:
        session.partitiontable.create({
            'name': name,
            'template': PARTITION_SCRIPT_DATA_FILE}
        )
        session.partitiontable.clone({
            'name': new_name,
            'default': True,
            'snippet': False,
            'os_family_selection': os_family_selection,
            'audit_comment': audit_comment,
        }, name)
        pt = session.partitiontable.read(new_name)
        assert pt['os_family_selection']['os_family'] == \
            os_family_selection['os_family']
        assert pt['name'] == new_name
