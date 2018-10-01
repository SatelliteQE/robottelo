from nailgun import entities

from robottelo.constants import (
    ENVIRONMENT,
    DEFAULT_CV,
    DOCKER_REGISTRY_HUB,
    REPO_TYPE
)
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
def module_docker_cr(module_org):
    docker_url = settings.docker.external_url
    return entities.DockerComputeResource(
        organization=[module_org],
        url=docker_url,
    ).create()


@fixture(scope='module')
def module_prod(module_org):
    return entities.Product(organization=module_org).create()


@tier2
@upgrade
def test_positive_create_with_compresource(session,
                                           module_docker_cr, module_prod):
    """Create containers for a compute resource

    :id: 299fc13d-5c2f-4642-a6de-735c89fdd096

    :expectedresults: The docker container is created for the compute
        resource

    :CaseLevel: Integration
    """
    deploy_on = module_docker_cr.name + ' (Docker)'
    repo_name = gen_string('alpha')
    name = gen_string('alpha', 4)
    repo = entities.Repository(
        name=repo_name,
        url=DOCKER_REGISTRY_HUB,
        product=module_prod,
        content_type=REPO_TYPE['docker'],
        docker_upstream_name="centos"
    ).create()
    repo.sync()
    with session:
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
        assert session.container.search(name)[0]['Name'] == name
