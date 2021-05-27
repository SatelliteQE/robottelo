"""Test class for Products UI

:Requirement: Product

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: ContentManagement

:Assignee: ltran

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from datetime import timedelta

import pytest
from fauxfactory import gen_choice
from nailgun import entities

from robottelo.config import settings
from robottelo.constants import REPO_TYPE
from robottelo.constants import SYNC_INTERVAL
from robottelo.constants import VALID_GPG_KEY_FILE
from robottelo.constants.repos import FAKE_1_YUM_REPO
from robottelo.datafactory import gen_string
from robottelo.datafactory import parametrized
from robottelo.datafactory import valid_cron_expressions
from robottelo.datafactory import valid_data_list
from robottelo.helpers import read_data_file


@pytest.fixture(scope='module')
def module_org():
    return entities.Organization().create()


@pytest.mark.tier2
@pytest.mark.skipif((not settings.repos_hosting_url), reason='Missing repos_hosting_url')
def test_positive_end_to_end(session, module_org):
    """Perform end to end testing for product component

    :id: d0e1f0d1-2380-4508-b270-62c1d8b3e2ff

    :expectedresults: All expected CRUD actions finished successfully

    :CaseLevel: Integration

    :CaseImportance: Critical
    """
    product_name = gen_string('alpha')
    new_product_name = gen_string('alpha')
    product_label = gen_string('alpha')
    product_description = gen_string('alpha')
    gpg_key = entities.GPGKey(
        content=read_data_file(VALID_GPG_KEY_FILE), organization=module_org
    ).create()
    sync_plan = entities.SyncPlan(organization=module_org).create()
    with session:
        # Create new product using different parameters
        session.product.create(
            {
                'name': product_name,
                'label': product_label,
                'gpg_key': gpg_key.name,
                'sync_plan': sync_plan.name,
                'description': product_description,
            }
        )
        assert session.product.search(product_name)[0]['Name'] == product_name
        # Verify that created entity has expected parameters
        product_values = session.product.read(product_name)
        assert product_values['details']['name'] == product_name
        assert product_values['details']['label'] == product_label
        assert product_values['details']['gpg_key'] == gpg_key.name
        assert product_values['details']['description'] == product_description
        assert product_values['details']['sync_plan'] == sync_plan.name
        # Update a product with a different name
        session.product.update(product_name, {'details.name': new_product_name})
        assert session.product.search(product_name)[0]['Name'] != product_name
        assert session.product.search(new_product_name)[0]['Name'] == new_product_name
        # Add a repo to product
        session.repository.create(
            new_product_name,
            {
                'name': gen_string('alpha'),
                'repo_type': REPO_TYPE['yum'],
                'repo_content.upstream_url': FAKE_1_YUM_REPO,
            },
        )
        # Synchronize the product
        result = session.product.synchronize(new_product_name)
        assert result['result'] == 'success'
        product_values = session.product.read(new_product_name)
        assert product_values['details']['repos_count'] == '1'
        assert product_values['details']['sync_state'] == 'Syncing Complete.'
        # Delete product
        session.product.delete(new_product_name)
        assert session.product.search(new_product_name)[0]['Name'] != new_product_name


@pytest.mark.parametrize('product_name', **parametrized(valid_data_list('ui')))
@pytest.mark.tier2
def test_positive_create_in_different_orgs(session, product_name):
    """Create Product with same name but in different organizations

    :id: 469fc036-a48a-4c0a-9da9-33e73f903479

    :parametrized: yes

    :expectedresults: Product is created successfully in both
        organizations.

    :CaseLevel: Integration
    """
    orgs = [entities.Organization().create() for _ in range(2)]
    with session:
        for org in orgs:
            session.organization.select(org_name=org.name)
            session.product.create({'name': product_name, 'description': org.name})
            assert session.product.search(product_name)[0]['Name'] == product_name
            product_values = session.product.read(product_name)
            assert product_values['details']['description'] == org.name


@pytest.mark.tier2
def test_positive_product_create_with_create_sync_plan(session, module_org):
    """Perform Sync Plan Create from Product Create Page

    :id: 4a87b533-12b6-4d4e-8a99-4bb95efc4321

    :expectedresults: Ensure sync get created and assigned to Product.

    :CaseLevel: Integration

    :CaseImportance: Medium
    """
    product_name = gen_string('alpha')
    product_description = gen_string('alpha')
    gpg_key = entities.GPGKey(
        content=read_data_file(VALID_GPG_KEY_FILE), organization=module_org
    ).create()
    plan_name = gen_string('alpha')
    description = gen_string('alpha')
    cron_expression = gen_choice(valid_cron_expressions())
    with session:
        session.organization.select(module_org.name)
        startdate = session.browser.get_client_datetime() + timedelta(minutes=10)
        sync_plan_values = {
            'name': plan_name,
            'interval': SYNC_INTERVAL['custom'],
            'description': description,
            'cron_expression': cron_expression,
            'date_time.start_date': startdate.strftime("%Y-%m-%d"),
            'date_time.hours': startdate.strftime('%H'),
            'date_time.minutes': startdate.strftime('%M'),
        }
        session.product.create(
            {'name': product_name, 'gpg_key': gpg_key.name, 'description': product_description},
            sync_plan_values=sync_plan_values,
        )
        assert session.product.search(product_name)[0]['Name'] == product_name
        product_values = session.product.read(product_name, widget_names='details')
        assert product_values['details']['name'] == product_name
        assert product_values['details']['sync_plan'] == plan_name
        # Delete product
        session.product.delete(product_name)
        assert session.product.search(product_name)[0]['Name'] != product_name


@pytest.mark.stubbed
@pytest.mark.tier2
def test_positive_bulk_action_advanced_sync():
    """Advanced sync is available as a bulk action in the product.

    :id: 7e9bb306-452d-43b8-8725-604b4aebb222

    :customerscenario: true

    :BZ: 1759301

    :Steps:
        1. Enable or create a repository and sync it.
        2. Navigate to Content > Product > click on the product.
        3. Click Select Action > Advanced Sync.

    :expectedresults: Advanced sync for repositories can be run as a bulk action from the product.
    """
    pass
