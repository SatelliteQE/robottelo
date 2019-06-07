# -*- encoding: utf-8 -*-
"""Test class for module_streams UI

:Requirement: module_streams

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from fauxfactory import gen_string
from nailgun import entities
from robottelo.constants import (
    CUSTOM_MODULE_STREAM_REPO_2
)

from robottelo.decorators import fixture, tier2


@fixture(scope='module')
def module_org():
    return entities.Organization().create()


@fixture(scope='module')
def module_product(module_org):
    return entities.Product(organization=module_org).create()


@fixture(scope='module')
def module_yum_repo(module_product):
    yum_repo = entities.Repository(
        name=gen_string('alpha'),
        product=module_product,
        content_type='yum',
        url=CUSTOM_MODULE_STREAM_REPO_2,
    ).create()
    yum_repo.sync()
    return yum_repo


@tier2
def test_positive_module_stream_details_search_in_repo(session, module_org, module_yum_repo):
    """Create product with yum repository assigned to it. Search for
    module_streams inside of it

    :id: 2ad7021a-25ee-42de-97d9-21fd928591d3

    :expectedresults: Content search functionality works as intended and
        expected module_streams are present inside of repository

    :CaseLevel: Integration
    """
    with session:
        session.organization.select(org_name=module_org.name)
        assert session.modulestream.search('name = duck')[0]['Name'].startswith('duck')
        walrus_details = session.modulestream.read('walrus', '5.21')
        expected_module_details = {
            'Summary': 'Walrus 5.21 module',
            'Context': 'deadbeef',
            'Name': 'walrus',
            'Stream': '5.21',
            'Arch': 'x86_64',
            'Description': 'A module for the walrus 5.21 package',
        }
        module_stream_details = {
            key: value for key, value in
            walrus_details['details']['details_table'].items()
            if key in expected_module_details
        }
        assert expected_module_details == module_stream_details
