"""WebUI tests for the Docker feature.

:Requirement: Docker

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from types import SimpleNamespace

from nailgun import entities

from robottelo.api.utils import promote
from robottelo.config import settings
from robottelo.constants import (
    ENVIRONMENT,
    DEFAULT_CV,
    DOCKER_REGISTRY_HUB,
    REPO_TYPE
)
from robottelo.datafactory import gen_string
from robottelo.decorators import (
    fixture,
    tier2,
    upgrade,
)
from robottelo.vm import VirtualMachine


@fixture(scope='module')
def module_org():
    return entities.Organization().create()


@fixture(scope='module')
def module_container_host(module_org, module_loc):
    with VirtualMachine(
        source_image=settings.docker.docker_image,
        tag='docker'
    ) as docker_host:
        docker_host.install_katello_ca()
        compute_resource = entities.DockerComputeResource(
            location=[module_loc],
            organization=[module_org],
            name=gen_string('alpha'),
            url='http://{0}:2375'.format(docker_host.ip_addr),
        ).create()
        lce = entities.LifecycleEnvironment(organization=module_org).create()
        repo = entities.Repository(
            content_type='docker',
            docker_upstream_name='busybox',
            product=entities.Product(organization=module_org).create(),
            url=DOCKER_REGISTRY_HUB,
        ).create()
        repo.sync()
        content_view = entities.ContentView(
            composite=False,
            organization=module_org,
            repository=[repo],
        ).create()
        content_view.publish()
        cvv = content_view.read().version[0].read()
        promote(cvv, lce.id)
        yield SimpleNamespace(
            compute_resource=compute_resource,
            compute_resource_name=compute_resource.name + ' (Docker)',
            content_view=content_view,
            content_view_version=cvv,
            host=docker_host,
            lce=lce,
            location=module_loc,
            organization=module_org,
            repository=repo,
        )
        # deleting all containers before compute resource cleanup, as otherwise it won't be
        # possible to access the list of containers on UI
        existing_containers = entities.AbstractDockerContainer(
            compute_resource=compute_resource).search()
        for container in existing_containers:
            container.delete()


@fixture
def external_registry(module_org, module_loc):
    registry = entities.Registry(
        location=[module_loc],
        organization=[module_org],
        url=settings.docker.external_registry_1
    ).create()
    yield registry
    registry.delete()


@tier2
@upgrade
def test_positive_create_with_external_compresource(session, module_loc):
    """Create containers for a compute resource

    :id: 299fc13d-5c2f-4642-a6de-735c89fdd096

    :expectedresults: The docker container is created for the compute
        resource

    :CaseLevel: Integration
    """
    name = gen_string('alpha', 4).lower()
    org = entities.Organization().create()
    docker_cr = entities.DockerComputeResource(
        organization=[org],
        location=[module_loc],
        url=settings.docker.external_url,
    ).create()
    deploy_on = docker_cr.name + ' (Docker)'
    repo = entities.Repository(
        url=DOCKER_REGISTRY_HUB,
        product=entities.Product(organization=org).create(),
        content_type=REPO_TYPE['docker'],
        docker_upstream_name="centos"
    ).create()
    repo.sync()
    with session:
        session.organization.select(org.name)
        session.container.create({
            'preliminary.compute_resource.deploy_on': deploy_on,
            'image.content_view.lifecycle_environment': ENVIRONMENT,
            'image.content_view.content_view': DEFAULT_CV,
            'image.content_view.repository': repo.name,
            'image.content_view.tag': 'centos7.2.1511',
            'image.content_view.capsule': settings.server.hostname,
            'configuration.name': name,
            'configuration.command': 'top',
            'environment.tty': True,
        })


@tier2
@upgrade
def test_positive_create_with_compresource(session, module_container_host):
    """Create containers for a compute resource

    :id: 4916c72f-e921-450c-8023-2ee516deaf25

    :expectedresults: The docker container is created for the compute
        resource

    :BZ: 1347658

    :CaseLevel: Integration
    """
    tag_name = 'latest'
    name = gen_string('alpha', 4).lower()
    with session:
        session.container.create({
            'preliminary.compute_resource.deploy_on': module_container_host.compute_resource_name,
            'image.content_view.lifecycle_environment': module_container_host.lce.name,
            'image.content_view.content_view': module_container_host.content_view.name,
            'image.content_view.repository': module_container_host.repository.name,
            'image.content_view.tag': tag_name,
            'configuration.name': name,
        })
        assert session.container.search(name)[0]['Name'].lower() == name
        container = session.container.read(name)
        assert container['properties']['Name'] == '/{}'.format(name)
        assert container['properties']['Image Tag'] == tag_name
        assert container['properties']['Running on'] == module_container_host.compute_resource_name


@tier2
def test_positive_power_on_off(session, module_container_host):
    """Create containers for a compute resource,
    then power them on and finally power them off

    :id: cc27bb6f-7fa4-4c87-bf7e-339f2f888717

    :expectedresults: The docker container is created and the power status
        is showing properly

    :BZ: 1683348

    :CaseLevel: Integration
    """
    container = entities.DockerHubContainer(
        compute_resource=module_container_host.compute_resource,
        location=[module_container_host.location],
        name=gen_string('alpha', 4).lower(),
        organization=[module_container_host.organization],
    ).create()
    with session:
        for status in ('Off', 'On'):
            session.container.set_power(container.name, status)
            assert session.container.search(container.name)[0]['Status'] == status


@tier2
@upgrade
def test_positive_create_with_external_registry(session, external_registry, module_container_host):
    """Create a container pulling an image from a custom external
    registry

    :id: e609b411-7533-4f65-917a-bed3672ae03c

    :expectedresults: The docker container is created and the image is
        pulled from the external registry

    :CaseLevel: Integration
    """
    repo_name = 'rhel'
    tag_name = 'latest'
    name = gen_string('alpha', 4).lower()
    with session:
        session.container.create({
            'preliminary.compute_resource.deploy_on': module_container_host.compute_resource_name,
            'image.external_registry.registry': external_registry.name,
            'image.external_registry.search': repo_name,
            'image.external_registry.tag': tag_name,
            'configuration.name': name,
        })
        assert session.container.search(name)[0]['Name'].lower() == name
        container = session.container.read(name)
        assert container['properties']['Image Repository'] == repo_name
        assert container['properties']['Image Tag'] == tag_name
        assert container['properties']['Running on'] == module_container_host.compute_resource_name


@tier2
def test_positive_delete(session, external_registry, module_container_host):
    """Delete containers in an external compute resource

    :id: e69808e7-6a0c-4310-b57a-2271ac61d11a

    :expectedresults: The docker containers are deleted

    :CaseLevel: Integration
    """
    container = entities.DockerHubContainer(
        compute_resource=module_container_host.compute_resource,
        location=[module_container_host.location],
        name=gen_string('alpha', 4).lower(),
        organization=[module_container_host.organization],
    ).create()
    with session:
        assert session.container.search(container.name)[0]['Name'].lower() == container.name
        session.container.delete(container.name)
        assert container.name not in [
            el['Name'] for el in session.container.search(container.name)]


@tier2
def test_positive_create_with_unix_socket(session, module_org, module_loc):
    """Create containers for a docker unix-socket compute resource

    :id: 756a76c2-e406-4172-b72a-ca40cf3645f6

    :expectedresults: The docker container is created for the compute
        resource

    :CaseLevel: Integration
    """
    tag_name = 'latest'
    name = gen_string('alpha', 4).lower()
    cr_internal = entities.DockerComputeResource(
        location=[module_loc],
        name=gen_string('alpha'),
        organization=[module_org],
        url=settings.docker.get_unix_socket_url(),
    ).create()
    lce = entities.LifecycleEnvironment(organization=module_org).create()
    repo = entities.Repository(
        content_type='docker',
        docker_upstream_name='centos',
        product=entities.Product(organization=module_org).create(),
        url=DOCKER_REGISTRY_HUB,
    ).create()
    repo.sync()
    content_view = entities.ContentView(
        composite=False,
        organization=module_org,
        repository=[repo],
    ).create()
    content_view.publish()
    cvv = content_view.read().version[0].read()
    promote(cvv, lce.id)
    cr_name = cr_internal.name + ' (Docker)'
    with session:
        session.container.create({
            'preliminary.compute_resource.deploy_on': cr_name,
            'image.content_view.lifecycle_environment': lce.name,
            'image.content_view.content_view': content_view.name,
            'image.content_view.repository': repo.name,
            'image.content_view.tag': tag_name,
            'configuration.name': name,
        })
        assert session.container.search(name)[0]['Name'].lower() == name
        container = session.container.read(name)
        assert container['properties']['Name'] == '/{}'.format(name)
        assert container['properties']['Image Tag'] == tag_name
        assert container['properties']['Running on'] == cr_name
