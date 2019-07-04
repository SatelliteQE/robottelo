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
from robottelo.constants import DOCKER_REGISTRY_HUB, DOCKER_UPSTREAM_NAME
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
            docker_upstream_name=DOCKER_UPSTREAM_NAME,
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
def test_positive_delete(session, module_container_host):
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
