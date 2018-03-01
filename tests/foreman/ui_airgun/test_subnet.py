from nailgun import entities


def test_positive_create(session):
    subnet = entities.Subnet()
    subnet.create_missing()
    name = subnet.name
    with session:
        session.subnet.create({
            'name': name,
            'network_address': subnet.network,
            'network_mask': subnet.mask,
            'boot_mode': 'Static',
        })
        assert session.subnet.search(name) == name
