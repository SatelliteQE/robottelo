# Repository Fixtures
import pytest
from fauxfactory import gen_string
from nailgun import entities

from robottelo.api.utils import enable_rhrepo_and_fetchid
from robottelo.constants import DEFAULT_ARCHITECTURE
from robottelo.constants import PRDS
from robottelo.constants import REPOS
from robottelo.constants import REPOSET


@pytest.fixture(scope='function')
def function_product(function_org):
    return entities.Product(organization=function_org).create()


@pytest.fixture(scope='module')
def rh_repo_gt_manifest(module_gt_manifest_org):
    """Use GT manifest org, creates RH tools repo, syncs and returns RH repo."""
    # enable rhel repo and return its ID
    rh_repo_id = enable_rhrepo_and_fetchid(
        basearch=DEFAULT_ARCHITECTURE,
        org_id=module_gt_manifest_org.id,
        product=PRDS['rhel'],
        repo=REPOS['rhst7']['name'],
        reposet=REPOSET['rhst7'],
        releasever=None,
    )
    # Sync step because repo is not synced by default
    rh_repo = entities.Repository(id=rh_repo_id).read()
    rh_repo.sync()
    return rh_repo


@pytest.fixture(scope="function")
def repo_setup():
    """
    This fixture is used to create an organization, product, repository, and lifecycle environment
    and once the test case gets completed then it performs the teardown of that.
    """
    repo_name = gen_string('alpha')
    org = entities.Organization().create()
    product = entities.Product(organization=org).create()
    repo = entities.Repository(name=repo_name, product=product).create()
    lce = entities.LifecycleEnvironment(organization=org).create()
    details = {'org': org, 'product': product, 'repo': repo, 'lce': lce}
    yield details
