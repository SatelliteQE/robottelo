from nailgun import entities

from robottelo.constants import DEFAULT_LOC, DEFAULT_ORG
from robottelo.datafactory import gen_string


def test_positive_create_with_one_character_name(session):
    name = gen_string('alpha', 1)
    template = gen_string('alpha')
    with session:
        session.partitiontable.create({'name': name, 'template': template})
        assert session.partitiontable.search(
            'name == ' + name)[0]['Name'] == name


def test_positive_create(session):
    name = gen_string('alpha')
    template = gen_string('alpha')
    with session:
        session.partitiontable.create(
            {'name': name,
             'default': True,
             'template': template})
        assert session.partitiontable.search(name)[0]['Name'] == name


def test_positive_create_os_family(session):
    name = gen_string('alpha')
    template = gen_string('alpha')
    with session:
        session.partitiontable.create({
            'name': name,
            'snippet': False,
            'os_family_selection': {'os_family': 'Debian'},
            'template': template,
        }, )
        pt = session.partitiontable.read(name)
        assert pt['os_family_selection']['os_family'] == 'Debian'
        assert session.partitiontable.search(name)[0]['Name'] == name


def test_positive_create_with_snippet(session):
    name = gen_string('alpha')
    template = gen_string('alpha')
    with session:
        session.partitiontable.create({
            'name': name,
            'snippet': True,
            'template': template
        }, )
        assert session.partitiontable.search(name)[0]['Name'] == name


def test_positive_create_with_audit_comment(session):
    name = gen_string('alpha')
    template = gen_string('alpha')
    audit_comment = gen_string('alpha')
    with session:
        session.partitiontable.create({
            'name': name,
            'audit_comment': audit_comment,
            'template': template
        }, )
        assert session.partitiontable.search(name)[0]['Name'] == name


def test_positive_create_loc_org(session):
    name = gen_string('alpha')
    template = gen_string('alpha')
    locations = entities.Location().create()
    organizations = entities.Organization().create()
    with session:
        session.partitiontable.create({
            'name': name,
            'locations.assigned': [locations.name],
            'organizations.assigned': [organizations.name],
            'template': template
        })
        pt = session.partitiontable.read(name)
        assert locations.name in pt['locations']['assigned']
        assert organizations.name in pt['organizations']['assigned']


def test_positive_delete_with_lock_and_unlock(session):
    name = gen_string('alpha')
    template = gen_string('alpha')
    audit_comment = gen_string('alpha')
    with session:
        session.partitiontable.create({
            'name': name,
            'default': True,
            'snippet': True,
            'audit_comment': audit_comment,
            'template': template
        }, )
        assert session.partitiontable.search(name)[0]['Name'] == name
        session.partitiontable.lock(name)
        try:
            session.partitiontable.delete(name)
        except ValueError:
            assert session.partitiontable.search(name)[0]['Name'] == name
        session.partitiontable.unlock(name)
        session.partitiontable.delete(name)
        assert not session.partitiontable.search(name)


def test_positive_create_default_for_organization(session):
    name = gen_string('alpha')
    template = gen_string('alpha')
    default_org = entities.Organization().search(
        query={'search': 'name="{0}"'.format(DEFAULT_ORG)})[0]
    with session:
        session.partitiontable.create({
            'name': name,
            'default': True,
            'organizations.assigned': [default_org.name],
            'template': template
        })
        session.organization.select(DEFAULT_ORG)
        assert session.partitiontable.search(name)[0]['Name'] == name


def test_positive_create_non_default_for_organization(session):
    name = gen_string('alpha')
    template = gen_string('alpha')
    organizations = entities.Organization().create()
    with session:
        session.partitiontable.create({
            'name': name,
            'default': False,
            'organizations.assigned': [organizations.name],
            'template': template
        })
        session.organization.select(org_name=organizations.name)
        assert session.partitiontable.search(name)[0]['Name'] == name


def test_positive_create_default_for_location(session):
    name = gen_string('alpha')
    template = gen_string('alpha')
    default_loc = entities.Location().search(
        query={'search': 'name="{0}"'.format(DEFAULT_LOC)})[0]
    with session:
        session.partitiontable.create({
            'name': name,
            'default': True,
            'locations.assigned': [default_loc.name],
            'template': template
        })
        session.location.select(DEFAULT_LOC)
        assert session.partitiontable.search(name)[0]['Name'] == name


def test_positive_create_non_default_for_location(session):
    name = gen_string('alpha')
    template = gen_string('alpha')
    locations = entities.Location().create()
    with session:
        session.partitiontable.create({
            'name': name,
            'default': False,
            'locations.assigned': [locations.name],
            'template': template
        })
        session.location.select(loc_name=locations.name)
        assert session.partitiontable.search(name)[0]['Name'] == name


def test_positive_update(session):
    old_name = gen_string('alpha')
    new_name = gen_string('alpha')
    template = gen_string('alpha')
    template_new = gen_string('alpha')
    os_family_selection = {'os_family': 'Red Hat'}
    new_os_fs = {'os_family': 'Debian'}
    with session:
        session.partitiontable.create({
            'name': old_name,
            'template': template,
            'os_family_selection': os_family_selection,
        })
        session.partitiontable.update({
            'name': new_name,
            'os_family_selection': new_os_fs,
            'template': template_new,
        }, old_name)
        pt = session.partitiontable.read(new_name)
        assert pt['os_family_selection']['os_family'] == new_os_fs['os_family']
        assert pt['name'] == new_name


def test_positive_clone(session):
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    template = gen_string('alpha')
    template_new = gen_string('alpha')
    audit_comment = gen_string('alpha')
    os_fm_sl = {'os_family': 'Red Hat'}
    with session:
        session.partitiontable.create({'name': name, 'template': template})
        session.partitiontable.clone({
            'name': new_name,
            'default': True,
            'snippet': False,
            'os_family_selection': os_fm_sl,
            'audit_comment': audit_comment,
            'template': template_new
        }, name)
        pt = session.partitiontable.read(new_name)
        assert pt['os_family_selection']['os_family'] == os_fm_sl['os_family']
        assert pt['name'] == new_name
