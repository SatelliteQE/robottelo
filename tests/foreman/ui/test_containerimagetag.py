"""WebUI tests for the Docker Image Tags feature.

:Requirement: Docker Image Tag

:CaseAutomation: Automated

:CaseComponent: ContainerManagement-Content

:team: Phoenix-content

:CaseImportance: High

"""

import pytest

from robottelo.constants import (
    CONTAINER_REGISTRY_HUB,
    CONTAINER_UPSTREAM_NAME,
    DEFAULT_CV,
    ENVIRONMENT,
    REPO_TYPE,
)
from robottelo.utils.issue_handlers import is_open


@pytest.fixture(scope="module")
def module_org(module_target_sat):
    return module_target_sat.api.Organization().create()


@pytest.fixture(scope="module")
def module_product(module_org, module_target_sat):
    return module_target_sat.api.Product(organization=module_org).create()


@pytest.fixture(scope="module")
def module_repository(module_product, module_target_sat):
    repo = module_target_sat.api.Repository(
        content_type=REPO_TYPE['docker'],
        docker_upstream_name=CONTAINER_UPSTREAM_NAME,
        product=module_product,
        url=CONTAINER_REGISTRY_HUB,
    ).create()
    repo.sync(timeout=1440)
    return repo


@pytest.mark.tier2
def test_positive_search(session, module_org, module_product, module_repository):
    """Search for a docker image tag and reads details of it

    :id: 28640396-c44d-4487-9d6d-3d5f2ed599d7

    :expectedresults: The docker image tag can be searched and found,
        details are read

    :BZ: 2009069, 2242515
    """
    with session:
        session.organization.select(org_name=module_org.name)
        search = session.containerimagetag.search('latest')
        if not is_open('BZ:2242515'):
            assert module_product.name in [i['Product Name'] for i in search]
        values = session.containerimagetag.read('latest')
        if not is_open('BZ:2242515'):
            assert module_product.name == values['details']['product']
        assert values['lce']['table'][0]['Environment'] == ENVIRONMENT
        repo_line = next(
            (item for item in values['repos']['table'] if item['Name'] == module_repository.name),
            None,
        )
        assert module_product.name == repo_line['Product']
        assert repo_line['Content View'] == DEFAULT_CV
        assert 'Success' in repo_line['Last Sync']
