from robottelo.datafactory import gen_string


def test_positive_create(session):
    ak_name = gen_string('alpha')
    with session:
        session.activationkey.create({
            'name': ak_name,
            'unlimited_hosts': False,
            'max_hosts': 2,
            'description': gen_string('alpha'),
        })
        assert session.activationkey.search(ak_name) == ak_name
