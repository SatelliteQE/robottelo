"""Test class for Ostree Branch CLI.

:Requirement: Ostreebranch

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: ContentManagement

:Assignee: ltran

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import random

import pytest
from nailgun import entities

from robottelo.cli.contentview import ContentView
from robottelo.cli.factory import make_content_view
from robottelo.cli.factory import make_org_with_credentials
from robottelo.cli.factory import make_product_with_credentials
from robottelo.cli.factory import make_repository_with_credentials
from robottelo.cli.ostreebranch import OstreeBranch
from robottelo.cli.repository import Repository
from robottelo.config import settings
from robottelo.constants.repos import OSTREE_REPO
from robottelo.decorators.host import skip_if_os

pytestmark = [
    pytest.mark.skipif((not settings.repos_hosting_url), reason='Missing repos_hosting_url'),
    pytest.mark.tier3,
]


@pytest.fixture(scope='module')
def ostree_user_credentials():
    password = 'password'
    user = entities.User(admin=True, password=password).create()
    return user.login, password


@pytest.fixture(scope='module')
def ostree_repo_with_user(ostree_user_credentials):
    """Create an user, organization, product and ostree repo,
    sync ostree repo for particular user,
    create content view and publish it for particular user
    """
    org = make_org_with_credentials(credentials=ostree_user_credentials)
    product = make_product_with_credentials(
        {'organization-id': org['id']}, ostree_user_credentials
    )
    # Create new custom ostree repo
    ostree_repo = make_repository_with_credentials(
        {
            'product-id': product['id'],
            'content-type': 'ostree',
            'publish-via-http': 'false',
            'url': OSTREE_REPO,
        },
        ostree_user_credentials,
    )
    Repository.with_user(*ostree_user_credentials).synchronize({'id': ostree_repo['id']})
    cv = make_content_view(
        {'organization-id': org['id'], 'repository-ids': [ostree_repo['id']]},
        ostree_user_credentials,
    )
    ContentView.with_user(*ostree_user_credentials).publish({'id': cv['id']})
    cv = ContentView.with_user(*ostree_user_credentials).info({'id': cv['id']})
    return {'cv': cv, 'org': org, 'ostree_repo': ostree_repo, 'product': product}


@skip_if_os('RHEL6')
@pytest.mark.skip_if_open("BZ:1625783")
def test_positive_list(ostree_user_credentials, ostree_repo_with_user):
    """List Ostree Branches

    :id: 0f5e7e63-c0e3-43fc-8238-caf19a478a46

    :expectedresults: Ostree Branch List is displayed
    """
    result = OstreeBranch.with_user(*ostree_user_credentials).list()
    assert len(result) > 0


@skip_if_os('RHEL6')
@pytest.mark.upgrade
def test_positive_list_by_repo_id(ostree_repo_with_user, ostree_user_credentials):
    """List Ostree branches by repo id

    :id: 8cf1a973-031c-4c02-af14-0faba22ab60b

    :expectedresults: Ostree Branch List is displayed

    """

    branch = OstreeBranch.with_user(*ostree_user_credentials)
    result = branch.list({'repository-id': ostree_repo_with_user['ostree_repo']['id']})
    assert len(result) > 0


@skip_if_os('RHEL6')
@pytest.mark.skip_if_open("BZ:1625783")
def test_positive_list_by_product_id(ostree_repo_with_user, ostree_user_credentials):
    """List Ostree branches by product id

    :id: e7b9d04d-cace-4271-b166-214017200c53

    :expectedresults: Ostree Branch List is displayed
    """
    result = OstreeBranch.with_user(*ostree_user_credentials).list(
        {'product-id': ostree_repo_with_user['product']['id']}
    )
    assert len(result) > 0


@skip_if_os('RHEL6')
@pytest.mark.skip_if_open("BZ:1625783")
def test_positive_list_by_org_id(ostree_repo_with_user, ostree_user_credentials):
    """List Ostree branches by org id

    :id: 5b169619-305f-4934-b363-068193330701

    :expectedresults: Ostree Branch List is displayed
    """
    result = OstreeBranch.with_user(*ostree_user_credentials).list(
        {'organization-id': ostree_repo_with_user['org']['id']}
    )
    assert len(result) > 0


@skip_if_os('RHEL6')
@pytest.mark.skip_if_open("BZ:1625783")
def test_positive_list_by_cv_id(ostree_repo_with_user, ostree_user_credentials):
    """List Ostree branches by cv id

    :id: 3654f107-44ee-4af2-a9e4-f9fd8c68491e

    :expectedresults: Ostree Branch List is displayed

    """
    result = OstreeBranch.with_user(*ostree_user_credentials).list(
        {'content-view-id': ostree_repo_with_user['cv']['id']}
    )
    assert len(result) > 0


@skip_if_os('RHEL6')
@pytest.mark.skip_if_open("BZ:1625783")
def test_positive_info_by_id(ostree_user_credentials, ostree_repo_with_user):
    """Get info for Ostree branch by id

    :id: 7838c9a8-56da-44de-883c-28571ecfa75c

    :expectedresults: Ostree Branch Info is displayed
    """
    result = OstreeBranch.with_user(*ostree_user_credentials).list()
    assert len(result) > 0
    # Grab a random branch
    branch = random.choice(result)
    result = OstreeBranch.with_user(*ostree_user_credentials).info({'id': branch['id']})
    assert branch['id'] == result['id']
