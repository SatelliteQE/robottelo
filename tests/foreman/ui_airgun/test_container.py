from nailgun import entities

from robottelo.constants import ENVIRONMENT, DEFAULT_CV, DOCKER_REGISTRY_HUB, REPO_TYPE
from robottelo.datafactory import gen_string
from robottelo.decorators import fixture
from robottelo.config import settings
from robottelo.decorators import (
    tier2,
    upgrade,
)


@fixture(scope='module')
def module_org():
    return entities.Organization().create()


@fixture(scope='module')
def create_docker(module_org):
    docker_url = settings.docker.external_url
    return entities.DockerComputeResource(
        name=gen_string('alpha'),
        organization=[module_org],
        url=docker_url,
    ).create()


@fixture(scope='module')
def module_prod(module_org):
    return entities.Product(organization=module_org).create()


@tier2
@upgrade
def test_positive_create_with_compresource(session, create_docker, module_prod):
    """Create containers for a compute resource

    :id: 299fc13d-5c2f-4642-a6de-735c89fdd096

    :expectedresults: The docker container is created for the compute
        resource

    :CaseLevel: Integration
    """
    deploy_on = create_docker.name + ' (Docker)'
    lifecycle_environment = ENVIRONMENT
    content_view = DEFAULT_CV
    repo_name = gen_string('alpha')
    container_name = gen_string('alpha')
    upstream_repository_name = "centos"
    repo = entities.Repository(
        name=repo_name,
        url=DOCKER_REGISTRY_HUB,
        product=module_prod,
        content_type=REPO_TYPE['docker'],
        docker_upstream_name=upstream_repository_name
    ).create()
    repo.sync()
    with session:
        session.container.create({
            'ContainerPreliminaryCreateView.compute_resource.deploy_on': deploy_on,
            'ContainerImageCreateView.content_view.lifecycle_environment': lifecycle_environment,
            'ContainerImageCreateView.content_view.content_view': content_view,
            'ContainerImageCreateView.content_view.repository': repo.name,
            'ContainerImageCreateView.content_view.tag': '7',
            'ContainerImageCreateView.content_view.capsule': settings.server.hostname,
            'ContainerConfigurationCreateView.name': container_name,
            'ContainerConfigurationCreateView.command': 'top',
            'ContainerEnvironmentCreateView.tty': True,
        })
