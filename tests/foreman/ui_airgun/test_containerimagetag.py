"""WebUI tests for the Docker Image Tags feature.

:Requirement: Docker Image Tag

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from nailgun import entities

from robottelo.constants import (
    ENVIRONMENT,
    DOCKER_REGISTRY_HUB,
    DOCKER_UPSTREAM_NAME,
    REPO_TYPE,
)
from robottelo.decorators import fixture, tier2


@fixture(scope="module")
def module_org():
    return entities.Organization().create()


@fixture(scope="module")
def module_product(module_org):
    return entities.Product(organization=module_org).create()


@fixture(scope="module")
def module_repository(module_product):
    repo = entities.Repository(
        content_type=REPO_TYPE['docker'],
        docker_upstream_name=DOCKER_UPSTREAM_NAME,
        product=module_product,
        url=DOCKER_REGISTRY_HUB,
    ).create()
    repo.sync()
    return repo


@tier2
def test_positive_search(
        session, module_org, module_product, module_repository):
    """Search for a docker image tag and reads details of it

    :id: 28640396-c44d-4487-9d6d-3d5f2ed599d7

    :expectedresults: The docker image tag can be searched and found,
        details are read

    :CaseLevel: Integration
    """
    with session:
        session.organization.select(org_name=module_org.name)
        search = session.containerimagetag.search('latest')
        assert module_product.name == search[0]['Product Name']
        assert module_repository.name == search[0]['Repository Name']
        values = session.containerimagetag.read('latest')
        assert module_product.name == values['details']['product']
        assert module_repository.name == values['details']['repository']
        assert values['lce']['table'][0]['Environment'] == ENVIRONMENT
