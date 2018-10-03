"""WebUI tests for the Docker Image Tags feature.

:Requirement: Docker

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from nailgun import entities

from robottelo.decorators import fixture, tier2


@fixture(scope="module")
def org():
    return entities.Organization().create()


@fixture(scope="module")
def product(org):
    return entities.Product(organization=org).create()


@fixture(scope="module")
def sync_repo(product):
    repo = entities.Repository(
        content_type='docker',
        docker_upstream_name='busybox',
        product=product,
        url=u'https://registry-1.docker.io',
    ).create()
    repo.sync()
    return repo


@tier2
def test_positive_search(session, org, product, sync_repo):
    """Search for a docker image

    :id: 28640396-c44d-4487-9d6d-3d5f2ed599d7

    :expectedresults: The docker tag can be searched and found

    :CaseLevel: Integration
    """
    with session:
        session.organization.select(org_name=org.name)
        search = session.containerimagetag.search('latest')
        assert product.name == search[0]['Product Name']
        assert sync_repo.name == search[0]['Repository Name']


def test_positve_read_details(session, org, product, sync_repo):
    with session:
        session.organization.select(org_name=org.name)
        values = session.containerimagetag.read('latest')
        assert product.name == values['details']['product']
        assert sync_repo.name == values['details']['repository']
        assert values['lce']['table'][0]['Environment'] == 'Library'
