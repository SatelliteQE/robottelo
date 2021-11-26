# Host Specific Fixtures
import pytest
from nailgun import entities

from robottelo.cli.factory import setup_org_for_a_rh_repo
from robottelo.constants import PRDS
from robottelo.constants import REPOS
from robottelo.constants import REPOSET


@pytest.fixture(scope='module')
def module_host():
    return entities.Host().create()


@pytest.fixture(scope='module')
def module_model():
    return entities.Model().create()


@pytest.mark.skip_if_not_set('clients', 'fake_manifest')
@pytest.fixture(scope="module")
def setup_rhst_repo():
    """Prepare Satellite tools repository for usage in specified organization"""
    org = entities.Organization().create()
    cv = entities.ContentView(organization=org).create()
    lce = entities.LifecycleEnvironment(organization=org).create()
    ak = entities.ActivationKey(
        environment=lce,
        organization=org,
    ).create()
    repo_name = 'rhst7'
    setup_org_for_a_rh_repo(
        {
            'product': PRDS['rhel'],
            'repository-set': REPOSET[repo_name],
            'repository': REPOS[repo_name]['name'],
            'organization-id': org.id,
            'content-view-id': cv.id,
            'lifecycle-environment-id': lce.id,
            'activationkey-id': ak.id,
        }
    )
    return {'ak': ak, 'cv': cv, 'lce': lce, 'org': org, 'repo_name': repo_name}
