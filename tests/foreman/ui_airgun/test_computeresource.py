from robottelo.datafactory import gen_string, valid_data_list
from robottelo.decorators import fixture, parametrize
from robottelo.config import settings
from nailgun import entities
from robottelo.constants import FOREMAN_PROVIDERS
import pytest


@fixture(scope='module')
def module_org():
    return entities.Organization().create()


@parametrize('name', **valid_data_list('ui'))
def test_positive_create_docker(session, name):
    docker_url = settings.docker.external_url
    with session:
        session.computeresource.create({
            'name': name,
            'description': gen_string('alpha'),
            'provider': FOREMAN_PROVIDERS['docker'],
            'provider_content.url': docker_url,
        })
        assert session.computeresource.search(name)[0]['Name'] == name


@parametrize('name', **valid_data_list('ui'))
def test_positive_create_ec2(session, name):
    ec2_access_key = settings.ec2.access_key
    ec2_secret_key = settings.ec2.secret_key
    with session:
        session.computeresource.create({
            'name': name,
            'description': gen_string('alpha'),
            'provider': FOREMAN_PROVIDERS['ec2'],
            'provider_content.access_key': ec2_access_key,
            'provider_content.secret_key': ec2_secret_key,
        })
        assert session.computeresource.search(name)[0]['Name'] == name


@parametrize('name', **valid_data_list('ui'))
def test_positive_create_libvirt(session, name):
    libvirt_url = settings.compute_resources.libvirt_hostname
    with session:
        session.computeresource.create({
            'name': name,
            'description': gen_string('alpha'),
            'provider': FOREMAN_PROVIDERS['libvirt'],
            'provider_content.url': libvirt_url,
            'provider_content.display_type': 'VNC',
            'provider_content.console_passwords': True,
        })
        assert session.computeresource.search(name)[0]['Name'] == name


@parametrize('name', **valid_data_list('ui'))
def test_positive_create_vmware(session, name):
    vmware_vcenter = settings.vmware.vcenter
    vmware_user = settings.vmware.username
    vmware_password = settings.vmware.password
    with session:
        session.computeresource.create({
            'name': name,
            'description': gen_string('alpha'),
            'provider': FOREMAN_PROVIDERS['vmware'],
            'provider_content.vcenter': vmware_vcenter,
            'provider_content.user': vmware_user,
            'provider_content.password': vmware_password,
        })
        assert session.computeresource.search(name)[0]['Name'] == name


@parametrize('name', **valid_data_list('ui'))
def test_positive_create_rhv(session, name):
    rhev_url = settings.rhev.hostname
    username = settings.rhev.username
    password = settings.rhev.password
    with session:
        session.computeresource.create({
            'name': name,
            'description': gen_string('alpha'),
            'provider': FOREMAN_PROVIDERS['rhev'],
            'provider_content.url': rhev_url,
            'provider_content.user': username,
            'provider_content.password': password,
        })
        assert session.computeresource.search(name)[0]['Name'] == name


def test_positive_rename(session):
    name = gen_string('alpha')
    ak_name = gen_string('alpha')
    docker_url = settings.docker.external_url
    with session:
        session.computeresource.create({
            'name': name,
            'description': gen_string('alpha'),
            'provider': FOREMAN_PROVIDERS['docker'],
            'provider_content.url': docker_url,
        })
        session.computeresource.edit(name, {
            'name': ak_name,
        })
        assert session.computeresource.search(ak_name)[0]['Name'] == ak_name


def test_positive_delete(session):
    name = gen_string('alpha')
    docker_url = settings.docker.external_url
    with session:
        session.computeresource.create({
            'name': name,
            'description': gen_string('alpha'),
            'provider': FOREMAN_PROVIDERS['docker'],
            'provider_content.url': docker_url,
        })
        session.computeresource.delete(name)
        assert not session.computeresource.search(name)


@pytest.mark.parametrize("version,expected", [
    ('4', True),
    ('3', False),
])
def test_positive_create_rhev(session, version, expected):
    """Create new RHEV Compute Resource using APIv3(4) and autoloaded cert"""
    rhev_url = settings.rhev.hostname
    username = settings.rhev.username
    password = settings.rhev.password
    name = gen_string('alpha')
    with session:
        session.computeresource.create({
            'name': name,
            'provider': FOREMAN_PROVIDERS['rhev'],
            'provider_content.url': rhev_url,
            'provider_content.user': username,
            'provider_content.password': password,
            'provider_content.api4': expected,
        })
        assert session.computeresource.search(name)[0]['Name'] == name
        assert session.computeresource.read(
            name)['provider_content']['api4'] == expected


@parametrize('description', **valid_data_list('ui'))
@pytest.mark.parametrize('version', [
    '3',
    '4',
])
def test_positive_edit_rhev(session, module_org, description, version):
    """Edit a RHEV Compute Resource using APIv3 """
    """and  APIv4 - change description"""
    rhev_url = settings.rhev.hostname
    username = settings.rhev.username
    password = settings.rhev.password
    cr = entities.OVirtComputeResource(
        url=rhev_url, user=username, password=password,
        organization=[module_org], use_v4=version == 3).create()
    with session:
        session.computeresource.edit(
            name=cr.name, values={'description': description})
        assert session.computeresource.read(
            cr.name)['description'] == description
