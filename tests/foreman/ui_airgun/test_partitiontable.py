from nailgun import entities

from robottelo.datafactory import gen_string


def test_positive_create(session):
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
        assert session.partitiontable.search(name) == name
        session.partitiontable.lock(name)
        try:
            session.partitiontable.delete(name)
        except ValueError:
            assert session.partitiontable.search(name) == name
        session.partitiontable.unlock(name)
        session.partitiontable.delete(name)
        assert session.partitiontable.search(name) is None


def test_positive_create_os_family(session):
    name = gen_string('alpha')
    template = gen_string('alpha')
    with session:
        session.partitiontable.create({
            'name': name,
            'snippet': False,
            'os_family': 'Debian',
            'template': template,
        }, )
        assert session.partitiontable.search(name) == name


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


def test_positive_clone(session):
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    template = gen_string('alpha')
    template_new = gen_string('alpha')
    audit_comment = gen_string('alpha')
    with session:
        session.partitiontable.create({'name': name, 'template': template})
        session.partitiontable.clone({
            'name': new_name,
            'default': True,
            'snippet': False,
            'os_family': 'Red Hat',
            'audit_comment': audit_comment,
            'template': template_new
        }, name)
        pt = session.partitiontable.read(new_name)
        assert pt['os_family'] == 'Red Hat'
        assert pt['name'] == new_name
