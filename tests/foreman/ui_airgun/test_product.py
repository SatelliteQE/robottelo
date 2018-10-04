"""Test class for Products UI

:Requirement: Product

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from nailgun import entities

from robottelo.datafactory import valid_data_list
from robottelo.decorators import parametrize, tier2


@parametrize('product_name', **valid_data_list('ui'))
@tier2
def test_positive_create_in_different_orgs(session, product_name):
    """Create Product with same name but in different organizations

    :id: 469fc036-a48a-4c0a-9da9-33e73f903479

    :expectedresults: Product is created successfully in both
        organizations.

    :CaseLevel: Integration
    """
    orgs = [entities.Organization().create() for _ in range(2)]
    with session:
        for org in orgs:
            session.organization.select(org_name=org.name)
            session.product.create(
                {'name': product_name, 'description': org.name})
            assert session.product.search(
                product_name)[0]['Name'] == product_name
            product_values = session.product.read(product_name)
            assert product_values['details']['description'] == org.name
