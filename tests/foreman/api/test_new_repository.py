"""Unit tests for the new ``repositories`` paths.

:Requirement: Repository

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: Repositories

:Assignee: chiggins

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from nailgun import entities
from requests.exceptions import HTTPError

from robottelo.api.utils import enable_rhrepo_and_fetchid
from robottelo.api.utils import upload_manifest
from robottelo.constants import PRDS
from robottelo.constants import REPOS
from robottelo.constants import REPOSET


@pytest.mark.tier1
def test_negative_disable_repository_with_cv(module_org, session_entitlement_manifest):
    """"""
    upload_manifest(module_org.id, session_entitlement_manifest.content)
    rh_repo_id = enable_rhrepo_and_fetchid(
        basearch='x86_64',
        org_id=module_org.id,
        product=PRDS['rhel'],
        repo=REPOS['rhst7']['name'],
        reposet=REPOSET['rhst7'],
        releasever=None,
    )
    rh_repo = entities.Repository(id=rh_repo_id).read()
    rh_repo.sync()
    cv = entities.ContentView(organization=module_org, repository=[rh_repo_id]).create()
    cv.publish()
    reposet = entities.RepositorySet(name=REPOSET['rhst7'], product=rh_repo.product).search()[0]
    data = {'basearch': 'x86_64', 'releasever': '7Server', 'product_id': rh_repo.product.id}
    with pytest.raises(HTTPError) as error:
        reposet.disable(data=data)
    assert error.value.response.status_code == 500
    assert (
        'Repository cannot be deleted since it has already been '
        'included in a published Content View' in error.value.response.text
    )
