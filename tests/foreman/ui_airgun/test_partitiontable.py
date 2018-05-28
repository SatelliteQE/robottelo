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

from robottelo.constants import (
    PARTITION_SCRIPT_DATA_FILE,
    DEFAULT_LOC,
    DEFAULT_ORG,
)

from robottelo.decorators import (
    run_only_on,
    tier1,
    tier2,
    upgrade
)
from robottelo.helpers import get_data_file

PARTITION_SCRIPT_DATA_FILE = get_data_file(PARTITION_SCRIPT_DATA_FILE)


@run_only_on('sat')
@tier1
def test_positive_create_with_one_character_name(session):
    """Create a Partition table with 1 character in name

    :id: 2b8ee84f-34d4-464f-8fcb-4xd9647e43f0

    :expectedresults: Partition table is created

    :BZ: 1229384

    :CaseImportance: Critical
    """
    name = gen_string('alpha', 1)
    with session:
        session.partitiontable.create({
            'name': name,
            'template': PARTITION_SCRIPT_DATA_FILE,
            'os_family_selection': {'os_family': 'Red Hat'},
             })
        assert session.partitiontable.search(
            'name == ' + name)[0]['Name'] == name


@run_only_on('sat')
@tier1
def test_positive_create_with_name(session):
    """Create a new partition table

    :id: 2dd8e34d-5a39-49d0-9bde-dd1cdf2db2ad

    :customerscenario: true

    :expectedresults: Partition table is created

    :CaseImportance: Critical
    """
    name = gen_string('alpha')
    with session:
        session.partitiontable.create({
            'name': name,
            'template': PARTITION_SCRIPT_DATA_FILE,
            'os_family_selection': {'os_family': 'Red Hat'},
        })
        assert session.partitiontable.search(name)[0]['Name'] == name


@run_only_on('sat')
@tier1
def test_positive_create_with_snippet(session):
    """Create a new partition table with enabled snippet option

    :id: 37bb748a-g3d1-4d88-954f-71634168072a

    :expectedresults: Partition table is created

    :CaseImportance: Critical
    """
    name = gen_string('alpha')
    with session:
        session.partitiontable.create({
            'name': name,
            'snippet': True,
            'template': PARTITION_SCRIPT_DATA_FILE
        }, )
        assert session.partitiontable.search(name)[0]['Name'] == name


@run_only_on('sat')
@tier1
def test_positive_create_with_audit_comment(session):
    """Create a new partition table with some text inputted into audit
    comment section

    :id: f17e16ff-b07f-44ec-af24-b9af460c35aa

    :expectedresults: Partition table is created

    :CaseImportance: Critical
    """
    name = gen_string('alpha')
    audit_comment = gen_string('alpha')
    with session:
        session.partitiontable.create({
            'name': name,
            'audit_comment': audit_comment,
            'template': PARTITION_SCRIPT_DATA_FILE
        }, )
        assert session.partitiontable.search(name)[0]['Name'] == name


@run_only_on('sat')
@tier2
def test_positive_create_default_for_organization(session):
    """Create new partition table with enabled 'default' option. Check
    that newly created organization has that partition table assigned to it

    :id: 91c64054-cd0c-4d4b-888b-17d42e2n8527

    :expectedresults: New partition table is created and is present in the
        list of selected partition tables for any new organization

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    org_name = DEFAULT_ORG
    with session:
        session.partitiontable.create({
            'name': name,
            'default': True,
            'organizations.assigned': [org_name],
            'template': PARTITION_SCRIPT_DATA_FILE
        })
        session.organization.select(DEFAULT_ORG)
        assert session.partitiontable.search(name)[0]['Name'] == name


@run_only_on('sat')
@tier2
def test_positive_create_custom_organization(session):
    """Create new partition table with disabled 'default' option. Check
    that newly created organization does not contain that partition table.

    :id: 69e6z3f0f-af1f-4aa2-8987-3e3b9a16be37

    :expectedresults: New partition table is created and is not present in
        the list of selected partition tables for any new organization

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    organizations = entities.Organization().create()
    with session:
        session.partitiontable.create({
            'name': name,
            'default': False,
            'organizations.assigned': [organizations.name],
            'template': PARTITION_SCRIPT_DATA_FILE
        })
        session.organization.select(org_name=organizations.name)
        assert session.partitiontable.search(name)[0]['Name'] == name


@run_only_on('sat')
@tier2
def test_positive_create_default_for_location(session):
    """Create new partition table with enabled 'default' option. Check
    that newly created location has that partition table assigned to it

    :id: 8df82e7c-2f33-4f0d-93f6-1f78ea4d750d

    :expectedresults: New partition table is created and is present in the
        list of selected partition tables for any new location

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    loc_name = DEFAULT_LOC
    with session:
        session.partitiontable.create({
            'name': name,
            'default': True,
            'locations.assigned': [loc_name],
            'template': PARTITION_SCRIPT_DATA_FILE
        })
        session.location.select(DEFAULT_LOC)
        assert session.partitiontable.search(name)[0]['Name'] == name


@run_only_on('sat')
@tier2
def test_positive_create_custom_location(session):
    """Create new partition table with disabled 'default' option. Check
    that newly created location does not contain that partition table.

    :id: 094d4583-76sb-48d4-a89a-23b90741fd6f

    :expectedresults: New partition table is created and is not present in
        the list of selected partition tables for any new location

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    locations = entities.Location().create()
    with session:
        session.partitiontable.create({
            'name': name,
            'default': False,
            'locations.assigned': [locations.name],
            'template': PARTITION_SCRIPT_DATA_FILE
        })
        session.location.select(loc_name=locations.name)
        assert session.partitiontable.search(name)[0]['Name'] == name


@run_only_on('sat')
@tier1
@upgrade
def test_positive_delete(session):
    """Delete a partition table

    :id: 405ed98a-4207-4bf8-899e-df7a7791850e

    :customerscenario: true

    :expectedresults: Partition table is deleted

    :CaseImportance: Critical
    """
    name = gen_string('alpha')
    with session:
        session.partitiontable.create({
            'name': name,
            'os_family_selection': {'os_family': 'Red Hat'},
            'template': PARTITION_SCRIPT_DATA_FILE
        }, )
        session.partitiontable.delete(name)
        assert not session.partitiontable.search(name)


@run_only_on('sat')
@tier1
def test_positive_update(session):
    """Update partition table with its name, layout and OS family

    :id: 63203508-7c73-4ce0-853e-64564y67bec3

    :customerscenario: true

    :expectedresults: Partition table is updated

    :CaseImportance: Critical
    """
    old_name = gen_string('alpha')
    new_name = gen_string('alpha')
    with session:
        session.partitiontable.create({
            'name': old_name,
            'os_family_selection': {'os_family': 'Debian'},
            'template': PARTITION_SCRIPT_DATA_FILE,

        })
        session.partitiontable.update({
            'name': new_name,
            'os_family_selection': {'os_family': 'Red Hat'},
            'template': PARTITION_SCRIPT_DATA_FILE,
        }, old_name)
        pt = session.partitiontable.read(new_name)
        assert pt['os_family_selection']['os_family'] == 'Red Hat'
        assert pt['name'] == new_name


@run_only_on('sat')
@tier1
def test_negative_update_name(session):
    """Update invalid name in partition table

    :id: 704e8336-e14a-4d1a-b9db-2f81c87f6evc

    :expectedresults: Partition table is not updated.  Appropriate error
        shown.

    :CaseImportance: Critical
    """
    name_1 = gen_string('alpha')
    name_2 = gen_string('alpha')
    with session:
        session.partitiontable.create({
            'name': name_1,
            'template': PARTITION_SCRIPT_DATA_FILE,
        })
        session.partitiontable.create({
            'name': name_2,
            'template': PARTITION_SCRIPT_DATA_FILE,
        })
        # update name 2 with existing name 1
        session.partitiontable.update({
            'name': name_1,
            'template': PARTITION_SCRIPT_DATA_FILE,
        }, name_2)
        # name doesn't change
        assert session.partitiontable.search(name_2)[0]['Name'] == name_2


def test_positive_delete_with_lock_and_unlock(session):
    """Lock and unlock the partition table,
    to prevent partition table from deletion.

        :id: 704e8336-e14a-4d1a-b9db-2f81c8ax68cc

        :expectedresults: Partition table is locked, cannot be deleted,
        unlocked and then successfully deleted.

        :CaseImportance: High
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


def test_positive_clone(session):
    """Clone the partition table from existing partition table
    and change parameters in cloned partition table

        :id: 7067855d-fd5g-987h-8713-sd78kb9845wf
        :expectedresults: Partition table is cloned.

        :CaseImportance: Critical
        """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    audit_comment = gen_string('alpha')
    os_fm_sl = {'os_family': 'Red Hat'}
    with session:
        session.partitiontable.create({
            'name': name,
            'template': PARTITION_SCRIPT_DATA_FILE}
        )
        session.partitiontable.clone({
            'name': new_name,
            'default': True,
            'snippet': False,
            'os_family_selection': os_fm_sl,
            'audit_comment': audit_comment,
        }, name)
        pt = session.partitiontable.read(new_name)
        assert pt['os_family_selection']['os_family'] == os_fm_sl['os_family']
        assert pt['name'] == new_name
