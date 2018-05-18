from nailgun import entities
from robottelo.datafactory import gen_string


def test_positive_create(session):
    name = gen_string('alpha')
    with session:
        session.computeprofile.create({'name': name})
        assert session.computeprofile.search(name)[0]['Name'] == name


def test_positive_rename(session):
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    entities.ComputeProfile(name=name).create()
    with session:
        session.computeprofile.rename(name, {'name': new_name})
        assert session.computeprofile.search(new_name)[0]['Name'] == new_name


def test_positive_delete(session):
    name = gen_string('alpha')
    entities.ComputeProfile(name=name).create()
    with session:
        session.computeprofile.delete(name)
        assert not session.computeprofile.search(name)
