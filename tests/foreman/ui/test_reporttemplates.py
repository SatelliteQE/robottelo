"""Test for Report Templates

:Requirement: Reports

:CaseAutomation: Automated

:CaseComponent: Reporting

:team: Endeavour

:CaseImportance: High

"""

import json
import os
from pathlib import Path, PurePath

from lxml import etree
import pytest

from robottelo.config import robottelo_tmp_dir, settings
from robottelo.constants import (
    FAKE_0_CUSTOM_PACKAGE_NAME,
    FAKE_1_CUSTOM_PACKAGE,
    FAKE_1_CUSTOM_PACKAGE_NAME,
    FAKE_2_CUSTOM_PACKAGE,
    PRDS,
    REPOS,
    REPOSET,
)
from robottelo.utils.datafactory import gen_string


@pytest.fixture(scope='module')
def module_setup_content(module_sca_manifest_org, module_target_sat):
    org = module_sca_manifest_org
    rh_repo_id = module_target_sat.api_factory.enable_rhrepo_and_fetchid(
        basearch='x86_64',
        org_id=org.id,
        product=PRDS['rhel'],
        repo=REPOS['rhst7']['name'],
        reposet=REPOSET['rhst7'],
        releasever=None,
    )
    rh_repo = module_target_sat.api.Repository(id=rh_repo_id).read()
    rh_repo.sync()
    custom_product = module_target_sat.api.Product(organization=org).create()
    custom_repo = module_target_sat.api.Repository(
        name=gen_string('alphanumeric').upper(), product=custom_product
    ).create()
    custom_repo.sync()
    lce = module_target_sat.api.LifecycleEnvironment(organization=org).create()
    cv = module_target_sat.api.ContentView(
        organization=org,
        repository=[rh_repo_id, custom_repo.id],
    ).create()
    cv.publish()
    cvv = cv.read().version[0].read()
    cvv.promote(data={'environment_ids': lce.id})
    ak = module_target_sat.api.ActivationKey(
        content_view=cv, organization=org, environment=lce
    ).create()
    all_content = ak.product_content(data={'content_access_mode_all': '1'})['results']
    content_label = [repo['label'] for repo in all_content if repo['name'] == custom_repo.name][0]
    ak.content_override(
        data={'content_overrides': [{'content_label': content_label, 'value': '1'}]}
    )
    return org, ak, cv, lce


@pytest.mark.stubbed
def test_negative_create_report_without_name(session):
    """A report template with empty name can't be created

    :id: 916ec1f8-c42c-4297-9c98-01e8b9f2f075

    :setup: User with reporting access rights

    :steps:

        1. Monitor -> Report Templates -> Create Template
        2. Insert any content but empty name
        3. Submit

    :expectedresults: A report should not be created and a warning should be displayed

    :CaseImportance: Medium
    """


@pytest.mark.stubbed
def test_negative_cannot_delete_locked_report(session):
    """Edit a report template

    :id: cd19b90d-830f-4efd-8cbc-d5e09a909a67

    :setup: User with reporting access rights, some report template that is locked

    :steps:

        1. Monitor -> Report Templates
        2. In the reports row, in Actions Column, try to click Delete

    :expectedresults: A report should not be deleted and the button should not even be clickable

    :CaseImportance: Medium
    """


@pytest.mark.stubbed
def test_positive_preview_report(session):
    """Preview a report

    :id: cd19b90d-836f-4efd-8cbc-d5e09a909a67

    :setup: User with reporting access rights, some report template

    :steps:

        1. Monitor -> Report Templates
        2. Open the report template
        3. Go to Preview tab

    :expectedresults: A report preview should be shown, with correct but
                      limited data (load_hosts macro should only list 10 records)

    :CaseImportance: Medium
    """


def test_positive_end_to_end(session, module_org, module_location):
    """Perform end to end testing for report template component's CRUD operations

    :id: b44d4cc8-a78e-47cf-9993-0bb871ac2c96

    :expectedresults: All expected CRUD actions finished successfully

    :CaseImportance: Critical
    """
    name = gen_string('alpha')
    content = gen_string('alpha')
    new_name = gen_string('alpha')
    clone_name = gen_string('alpha')
    input_name = gen_string('alpha')
    template_input = [
        {
            'name': input_name,
            'required': True,
            'input_type': 'User input',
            'input_content.description': gen_string('alpha'),
        }
    ]
    with session:
        # CREATE report template
        session.reporttemplate.create(
            {
                'template.name': name,
                'template.default': False,
                'template.template_editor.editor': content,
                'template.audit_comment': gen_string('alpha'),
                'inputs': template_input,
                'type.snippet': False,
                'organizations.resources.assigned': [module_org.name],
                'locations.resources.assigned': [module_location.name],
            }
        )
        # READ report template
        rt = session.reporttemplate.read(name)
        assert rt['template']['name'] == name
        assert rt['template']['default'] is False
        assert rt['template']['template_editor']['editor'] == content
        assert rt['inputs'][0]['name'] == template_input[0]['name']
        assert rt['inputs'][0]['required'] is template_input[0]['required']
        assert rt['inputs'][0]['input_type'] == template_input[0]['input_type']
        assert (
            rt['inputs'][0]['input_content']['description']
            == template_input[0]['input_content.description']
        )
        assert rt['type']['snippet'] is False
        assert rt['locations']['resources']['assigned'][0] == module_location.name
        assert rt['organizations']['resources']['assigned'][0] == module_org.name
        # UPDATE report template
        session.reporttemplate.update(name, {'template.name': new_name, 'type.snippet': True})
        rt = session.reporttemplate.read(new_name)
        assert rt['template']['name'] == new_name
        assert rt['template']['default'] is False
        assert rt['template']['template_editor']['editor'] == content
        assert rt['inputs'][0]['name'] == template_input[0]['name']
        assert rt['inputs'][0]['required'] is template_input[0]['required']
        assert rt['inputs'][0]['input_type'] == template_input[0]['input_type']
        assert (
            rt['inputs'][0]['input_content']['description']
            == template_input[0]['input_content.description']
        )
        assert rt['type']['snippet'] is True
        assert rt['locations']['resources']['assigned'][0] == module_location.name
        assert rt['organizations']['resources']['assigned'][0] == module_org.name
        # LOCK
        session.reporttemplate.lock(new_name)
        assert session.reporttemplate.is_locked(new_name) is True
        # UNLOCK
        session.reporttemplate.unlock(new_name)
        assert session.reporttemplate.is_locked(new_name) is False
        # CLONE
        session.reporttemplate.clone(new_name, {'template.name': clone_name})
        rt = session.reporttemplate.read(clone_name)
        assert rt['template']['name'] == clone_name
        assert rt['template']['default'] is False
        assert rt['template']['template_editor']['editor'] == content
        assert rt['inputs'][0]['name'] == input_name
        assert rt['inputs'][0]['required'] is True
        assert rt['inputs'][0]['input_type'] == 'User input'
        assert rt['type']['snippet'] is True
        assert rt['locations']['resources']['assigned'][0] == module_location.name
        assert rt['organizations']['resources']['assigned'][0] == module_org.name
        # EXPORT
        file_path = session.reporttemplate.export(new_name)
        assert os.path.isfile(file_path)
        with open(file_path) as dfile:
            assert content in dfile.read()
        # DELETE report template
        session.reporttemplate.delete(new_name)
        assert not session.reporttemplate.search(new_name)


@pytest.mark.rhel_ver_list([7, 8, 9])
@pytest.mark.upgrade
def test_positive_generate_registered_hosts_report(
    session, target_sat, module_setup_content, rhel_contenthost
):
    """Use provided Host - Registered Content Hosts report for testing

    :id: b44d4cd8-a78e-47cf-9993-0bb871ac2c96

    :expectedresults: The Host - Registered Content Hosts report is generated
                      and it contains created host with correct data

    :CaseImportance: High
    """
    client = rhel_contenthost
    org, ak, _, _ = module_setup_content
    client.register(org, None, ak.name, target_sat)
    assert client.subscribed
    with session:
        session.location.select('Default Location')
        result_json = session.reporttemplate.generate(
            'Host - Registered Content Hosts', values={'output_format': 'JSON'}
        )
        with open(result_json) as json_file:
            data_json = json.load(json_file)
        assert list(data_json[0].keys()) == [
            'Name',
            'Ip',
            'Operating System',
            'Subscriptions',
            'Applicable Errata',
            'Owner',
            'Kernel',
            'Latest kernel available',
        ]
        assert data_json[0]['Name'] == client.hostname
        assert data_json[0]['Operating System'].split()[-1] == client._redhat_release['VERSION_ID']


@pytest.mark.rhel_ver_match('N-1')
def test_positive_cloud_billing_azure_columns(
    target_sat, module_setup_content, rhel_contenthost, module_org, default_location
):
    """Use provided Host - Installed Products report with Azure cloud billing columns

    :id: a55d4cd8-b88e-47cf-9993-1bb871ac3c97

    :CaseComponent: Hosts

    :Team: Proton

    :Verifies: SAT-39184

    :expectedresults: The Host - Installed Products report is generated
                      with Azure columns when 'Include Azure' is checked

    :CaseImportance: High
    """
    client = rhel_contenthost
    org, ak, _, _ = module_setup_content
    client.register(org, None, ak.name, target_sat)
    assert client.subscribed

    # Get Azure facts from settings
    azure_facts = settings.azurerm.cloud_billing_facts

    # Write cloud facts to host and upload via subscription-manager
    facts_content = json.dumps(azure_facts, indent=2)

    # Ensure facts directory exists
    client.execute('mkdir -p /etc/rhsm/facts')

    # Write cloud facts to host-billing.facts
    client.execute(f"cat > /etc/rhsm/facts/host-billing.facts << 'EOF'\n{facts_content}\nEOF")

    # Verify file created correctly
    result = client.execute('cat /etc/rhsm/facts/host-billing.facts')
    assert result.status == 0, 'Failed to read facts file'

    # Upload facts to Satellite
    client.execute('subscription-manager facts --update')

    with target_sat.ui_session() as session:
        session.organization.select(module_org.name)
        session.location.select(default_location.name)
        result_json = session.reporttemplate.generate(
            'Host - Installed Products',
            values={'output_format': 'JSON', 'include_azure': 'yes'},
        )
        with open(result_json) as json_file:
            data_json = json.load(json_file)

        report_columns = data_json[0].keys()

        # Verify Azure columns are present
        assert 'Azure Subscription ID' in report_columns
        assert 'Azure Offer' in report_columns

        # Verify Azure fact values
        assert data_json[0]['Host Name'] == client.hostname
        assert data_json[0]['Azure Subscription ID'] == azure_facts['azure_subscription_id']
        assert data_json[0]['Azure Offer'] == azure_facts['azure_offer']


@pytest.mark.rhel_ver_match('N-1')
def test_positive_cloud_billing_aws_columns(
    target_sat, module_setup_content, rhel_contenthost, module_org, default_location
):
    """Use provided Host - Installed Products report with AWS cloud billing columns

    :id: b66d5cd9-c99f-48dg-0004-2cc982bd4d08

    :CaseComponent: Hosts

    :Team: Proton

    :Verifies: SAT-39184

    :expectedresults: The Host - Installed Products report is generated
                      with AWS columns when 'Include AWS' is checked

    :CaseImportance: High
    """
    client = rhel_contenthost
    org, ak, _, _ = module_setup_content
    client.register(org, None, ak.name, target_sat)
    assert client.subscribed

    # Get AWS facts from settings
    aws_facts = settings.ec2.cloud_billing_facts

    # Write cloud facts to host and upload via subscription-manager
    facts_content = json.dumps(aws_facts, indent=2)

    # Ensure facts directory exists
    client.execute('mkdir -p /etc/rhsm/facts')

    # Write cloud facts to host-billing.facts
    client.execute(f"cat > /etc/rhsm/facts/host-billing.facts << 'EOF'\n{facts_content}\nEOF")

    # Verify file created correctly
    result = client.execute('cat /etc/rhsm/facts/host-billing.facts')
    assert result.status == 0, 'Failed to read facts file'

    # Upload facts to Satellite
    client.execute('subscription-manager facts --update')

    with target_sat.ui_session() as session:
        session.organization.select(module_org.name)
        session.location.select(default_location.name)
        result_json = session.reporttemplate.generate(
            'Host - Installed Products',
            values={'output_format': 'JSON', 'include_aws': 'yes'},
        )
        with open(result_json) as json_file:
            data_json = json.load(json_file)

        report_columns = data_json[0].keys()

        # Verify AWS columns are present
        assert 'AWS Account ID' in report_columns
        assert 'AWS Billing Product' in report_columns
        assert 'AWS Instance Type' in report_columns
        assert 'AWS Marketplace Product' in report_columns

        # Verify AWS fact values
        assert data_json[0]['Host Name'] == client.hostname
        assert data_json[0]['AWS Account ID'] == str(aws_facts['aws_account_id'])
        assert data_json[0]['AWS Billing Product'] == aws_facts['aws_billing_products']
        assert data_json[0]['AWS Instance Type'] == aws_facts['aws_instance_type']
        assert data_json[0]['AWS Marketplace Product'] == aws_facts['aws_marketplace_product_codes']


@pytest.mark.rhel_ver_match('N-1')
def test_positive_cloud_billing_gcp_columns(
    target_sat, module_setup_content, rhel_contenthost, module_org, default_location
):
    """Use provided Host - Installed Products report with GCP cloud billing columns

    :id: c77d6ce0-d00g-59eh-1115-3dd093ce5e19

    :CaseComponent: Hosts

    :Team: Proton

    :Verifies: SAT-39184

    :expectedresults: The Host - Installed Products report is generated
                      with GCP columns when 'Include GCP' is checked

    :CaseImportance: High
    """
    client = rhel_contenthost
    org, ak, _, _ = module_setup_content
    client.register(org, None, ak.name, target_sat)
    assert client.subscribed

    # Get GCP facts from settings
    gcp_facts = settings.gce.cloud_billing_facts

    # Write cloud facts to host and upload via subscription-manager
    facts_content = json.dumps(gcp_facts, indent=2)

    # Ensure facts directory exists
    client.execute('mkdir -p /etc/rhsm/facts')

    # Write cloud facts to host-billing.facts
    client.execute(f"cat > /etc/rhsm/facts/host-billing.facts << 'EOF'\n{facts_content}\nEOF")

    # Verify file created correctly
    result = client.execute('cat /etc/rhsm/facts/host-billing.facts')
    assert result.status == 0, 'Failed to read facts file'

    # Upload facts to Satellite
    client.execute('subscription-manager facts --update')

    with target_sat.ui_session() as session:
        session.organization.select(module_org.name)
        session.location.select(default_location.name)
        result_json = session.reporttemplate.generate(
            'Host - Installed Products',
            values={'output_format': 'JSON', 'include_gcp': 'yes'},
        )
        with open(result_json) as json_file:
            data_json = json.load(json_file)

        report_columns = data_json[0].keys()

        # Verify GCP column is present
        assert 'GCP License Code' in report_columns

        # Verify GCP fact value
        assert data_json[0]['Host Name'] == client.hostname
        assert data_json[0]['GCP License Code'] == str(gcp_facts['gcp_license_codes'])


@pytest.mark.rhel_ver_match('N-1')
def test_positive_cloud_billing_inputs_default_false(
    target_sat, module_setup_content, rhel_contenthost, module_org, default_location
):
    """Verify cloud billing input fields default to false

    :id: d88e7df1-e11h-60fi-2226-4ee104df6f20

    :CaseComponent: Hosts

    :Team: Proton

    :Verifies: SAT-39184

    :expectedresults: When no cloud provider inputs are specified,
                      cloud billing columns do NOT appear in the report

    :CaseImportance: High
    """
    client = rhel_contenthost
    org, ak, _, _ = module_setup_content
    client.register(org, None, ak.name, target_sat)
    assert client.subscribed

    with target_sat.ui_session() as session:
        session.organization.select(module_org.name)
        session.location.select(default_location.name)
        result_json = session.reporttemplate.generate(
            'Host - Installed Products', values={'output_format': 'JSON'}
        )
        with open(result_json) as json_file:
            data_json = json.load(json_file)

        report_columns = data_json[0].keys()

        # Verify cloud billing columns do NOT appear by default
        assert 'Azure Subscription ID' not in report_columns
        assert 'Azure Offer' not in report_columns
        assert 'AWS Account ID' not in report_columns
        assert 'AWS Billing Product' not in report_columns
        assert 'AWS Instance Type' not in report_columns
        assert 'AWS Marketplace Product' not in report_columns
        assert 'GCP License Code' not in report_columns


@pytest.mark.rhel_ver_match('N-1')
def test_negative_cloud_billing_azure_false_aws_gcp_true(
    target_sat, module_setup_content, rhel_contenthost, module_org, default_location
):
    """Verify Azure cloud billing columns do NOT appear when Include Azure is false while AWS and GCP are true

    :id: e99f8eg2-f22i-71gj-3337-5ff215eg7g31

    :CaseComponent: Hosts

    :Team: Proton

    :Verifies: SAT-39184

    :expectedresults: When 'Include Azure' is false and AWS/GCP are true,
                      Azure columns do NOT appear but AWS and GCP columns DO appear

    :CaseImportance: High
    """
    client = rhel_contenthost
    org, ak, _, _ = module_setup_content
    client.register(org, None, ak.name, target_sat)
    assert client.subscribed

    with target_sat.ui_session() as session:
        session.organization.select(module_org.name)
        session.location.select(default_location.name)
        result_json = session.reporttemplate.generate(
            'Host - Installed Products',
            values={
                'output_format': 'JSON',
                'include_azure': 'no',
                'include_aws': 'yes',
                'include_gcp': 'yes',
            },
        )
        with open(result_json) as json_file:
            data_json = json.load(json_file)

        report_columns = data_json[0].keys()

        # Verify Azure columns do NOT appear
        assert 'Azure Subscription ID' not in report_columns
        assert 'Azure Offer' not in report_columns

        # Verify AWS and GCP columns DO appear
        assert 'AWS Account ID' in report_columns
        assert 'AWS Billing Product' in report_columns
        assert 'AWS Instance Type' in report_columns
        assert 'AWS Marketplace Product' in report_columns
        assert 'GCP License Code' in report_columns


@pytest.mark.rhel_ver_match('N-1')
def test_negative_cloud_billing_aws_false_azure_gcp_true(
    target_sat, module_setup_content, rhel_contenthost, module_org, default_location
):
    """Verify AWS cloud billing columns do NOT appear when Include AWS is false while Azure and GCP are true

    :id: f00g9fh3-g33j-82hk-4448-6gg326fh8h42

    :CaseComponent: Hosts

    :Team: Proton

    :Verifies: SAT-39184

    :expectedresults: When 'Include AWS' is false and Azure/GCP are true,
                      AWS columns do NOT appear but Azure and GCP columns DO appear

    :CaseImportance: High
    """
    client = rhel_contenthost
    org, ak, _, _ = module_setup_content
    client.register(org, None, ak.name, target_sat)
    assert client.subscribed

    with target_sat.ui_session() as session:
        session.organization.select(module_org.name)
        session.location.select(default_location.name)
        result_json = session.reporttemplate.generate(
            'Host - Installed Products',
            values={
                'output_format': 'JSON',
                'include_azure': 'yes',
                'include_aws': 'no',
                'include_gcp': 'yes',
            },
        )
        with open(result_json) as json_file:
            data_json = json.load(json_file)

        report_columns = data_json[0].keys()

        # Verify AWS columns do NOT appear
        assert 'AWS Account ID' not in report_columns
        assert 'AWS Billing Product' not in report_columns
        assert 'AWS Instance Type' not in report_columns
        assert 'AWS Marketplace Product' not in report_columns

        # Verify Azure and GCP columns DO appear
        assert 'Azure Subscription ID' in report_columns
        assert 'Azure Offer' in report_columns
        assert 'GCP License Code' in report_columns


@pytest.mark.rhel_ver_match('N-1')
def test_negative_cloud_billing_gcp_false_azure_aws_true(
    target_sat, module_setup_content, rhel_contenthost, module_org, default_location
):
    """Verify GCP cloud billing columns do NOT appear when Include GCP is false while Azure and AWS are true

    :id: g11h0gi4-h44k-93il-5559-7hh437gi9i53

    :CaseComponent: Hosts

    :Team: Proton

    :Verifies: SAT-39184

    :expectedresults: When 'Include GCP' is false and Azure/AWS are true,
                      GCP columns do NOT appear but Azure and AWS columns DO appear

    :CaseImportance: High
    """
    client = rhel_contenthost
    org, ak, _, _ = module_setup_content
    client.register(org, None, ak.name, target_sat)
    assert client.subscribed

    with target_sat.ui_session() as session:
        session.organization.select(module_org.name)
        session.location.select(default_location.name)
        result_json = session.reporttemplate.generate(
            'Host - Installed Products',
            values={
                'output_format': 'JSON',
                'include_azure': 'yes',
                'include_aws': 'yes',
                'include_gcp': 'no',
            },
        )
        with open(result_json) as json_file:
            data_json = json.load(json_file)

        report_columns = data_json[0].keys()

        # Verify GCP columns do NOT appear
        assert 'GCP License Code' not in report_columns

        # Verify Azure and AWS columns DO appear
        assert 'Azure Subscription ID' in report_columns
        assert 'Azure Offer' in report_columns
        assert 'AWS Account ID' in report_columns
        assert 'AWS Billing Product' in report_columns
        assert 'AWS Instance Type' in report_columns
        assert 'AWS Marketplace Product' in report_columns


@pytest.mark.rhel_ver_match('N-1')
def test_positive_cloud_billing_multiple_providers_enabled(
    target_sat, module_setup_content, rhel_contenthost, module_org, default_location
):
    """Verify multiple cloud billing provider options can be enabled simultaneously

    :id: h22i1hj5-i55l-04jm-6660-8ii548hj0j64

    :CaseComponent: Hosts

    :Team: Proton

    :Verifies: SAT-39184

    :expectedresults: When multiple cloud provider inputs are enabled,
                      all corresponding columns appear in the report

    :CaseImportance: High
    """
    client = rhel_contenthost
    org, ak, _, _ = module_setup_content
    client.register(org, None, ak.name, target_sat)
    assert client.subscribed

    with target_sat.ui_session() as session:
        session.organization.select(module_org.name)
        session.location.select(default_location.name)
        result_json = session.reporttemplate.generate(
            'Host - Installed Products',
            values={
                'output_format': 'JSON',
                'include_azure': 'yes',
                'include_aws': 'yes',
                'include_gcp': 'yes',
            },
        )
        with open(result_json) as json_file:
            data_json = json.load(json_file)

        report_columns = data_json[0].keys()

        # Verify all cloud provider columns appear
        assert 'Azure Subscription ID' in report_columns
        assert 'Azure Offer' in report_columns
        assert 'AWS Account ID' in report_columns
        assert 'AWS Billing Product' in report_columns
        assert 'AWS Instance Type' in report_columns
        assert 'AWS Marketplace Product' in report_columns
        assert 'GCP License Code' in report_columns


@pytest.mark.rhel_ver_match('N-1')
def test_positive_installed_products_hardware_model_column(
    target_sat, module_setup_content, rhel_contenthost, module_org, default_location
):
    """Use provided Host - Installed Products report with Hardware Model column

    :id: i33j2ik6-j66m-15kn-7771-9jj659ik1k75

    :CaseComponent: Hosts

    :Team: Proton

    :expectedresults: The Host - Installed Products report is generated
                      with Hardware Model column when 'Include Hardware Model' is checked

    :CaseImportance: High
    """
    client = rhel_contenthost
    org, ak, _, _ = module_setup_content
    client.register(org, None, ak.name, target_sat)
    assert client.subscribed

    # Create a hardware model
    hardware_model = target_sat.api.Model().create()

    # Associate the hardware model with the host
    host = target_sat.api.Host().search(query={'search': f'name={client.hostname}'})[0]
    host.model = hardware_model
    host.update(['model'])

    with target_sat.ui_session() as session:
        session.organization.select(module_org.name)
        session.location.select(default_location.name)
        result_json = session.reporttemplate.generate(
            'Host - Installed Products',
            values={'output_format': 'JSON', 'include_hardware_model': 'yes'},
        )
        with open(result_json) as json_file:
            data_json = json.load(json_file)

        report_columns = data_json[0].keys()

        # Verify Model column is present
        assert 'Model' in report_columns

        # Verify Model value
        assert data_json[0]['Host Name'] == client.hostname
        assert data_json[0]['Model'] == hardware_model.name


@pytest.mark.upgrade
def test_positive_generate_subscriptions_report_json(
    session, module_org, module_setup_content, module_target_sat
):
    """Use provided Subscriptions report, generate JSON

    :id: b44d4cd8-a88e-47cf-9993-0bb871ac2c96

    :expectedresults: The Subscriptions report is generated in JSON

    :CaseImportance: Medium
    """
    # generate Subscriptions report
    with module_target_sat.ui_session() as session:
        file_path = session.reporttemplate.generate(
            'Subscription - General Report', values={'output_format': 'JSON'}
        )
    with open(file_path) as json_file:
        data = json.load(json_file)
    subscription_cnt = len(module_target_sat.api.Subscription(organization=module_org).search())
    assert subscription_cnt > 0
    assert len(data) >= subscription_cnt
    keys_expected = [
        'Account number',
        'Available',
        'Contract number',
        'Days Remaining',
        'End date',
        'ID',
        'Name',
        'Organization',
        'Product Host Count',
        'Quantity',
        'SKU',
        'Start date',
    ]
    for subscription in data:
        assert sorted(list(subscription.keys())) == keys_expected


@pytest.mark.stubbed
def test_positive_applied_errata(session):
    """Generate an Applied Errata report

    :id: cd19b90d-836f-4efd-ccbc-d5e09a909a67
    :setup: User with reporting access rights, some host with applied errata
    :steps:
        1. Monitor -> Report Templates
        2. Applied Errata -> Generate
        3. Submit
    :expectedresults: A report is generated with all applied errata listed
    :CaseImportance: Medium
    """


@pytest.mark.stubbed
def test_datetime_picker(session):
    """Generate an Applied Errata report with date filled

    :id: cd19b90d-836f-4efd-c1bc-d5e09a909a67
    :setup: User with reporting access rights, some host with applied errata at
            time A, some host (can be the same host) with applied
            errata at time B>A and no errata applied at other time
    :steps:
        1. Monitor -> Report Templates
        2. Applied Errata -> Generate
        3. Fill in timeFrom>A
        4. Fill in B>timeTo
        5. Generate
    :expectedresults: A report is generated with all applied errata listed
                      that were generated before timeFrom and timeTo
    :CaseImportance: High
    """


@pytest.mark.stubbed
def test_positive_autocomplete(session):
    """Check if host field suggests matching hosts on typing

    :id: cd19b90d-836f-4efd-c2bc-d5e09a909a67
    :setup: User with reporting access rights, some Host, some report with host input
    :steps:
        1. Monitor -> Report Templates
        2. Host - Registered Content Hosts -> Generate
        3. Fill in part of the Host name
        4. Check if the Host is within suggestions
        5. Select the Host
        6. Submit
    :expectedresults: The same report is generated as if the host has been entered manually
    :CaseImportance: Medium
    """


def test_positive_schedule_generation_and_get_mail(
    session, module_sca_manifest_org, module_location, target_sat
):
    """Schedule generating a report. Request the result be sent via e-mail.

    :id: cd19b90d-836f-4efd-c3bc-d5e09a909a67
    :setup: User with reporting access rights, some Host, Org with imported manifest
    :steps:
        1. Monitor -> Report Templates
        2. Host - Registered Content Hosts -> Generate
        3. Set schedule to current time + 1 minute
        4. Check that the result should be sent via e-mail
        5. Submit
        6. Receive the e-mail
    :expectedresults: After ~1 minute, the same report is generated as if
                      the results were downloaded from WebUI.
                      The result is compressed.
    :CaseImportance: High
    """
    # make sure postfix daemon is running
    target_sat.execute('systemctl start postfix')
    # generate Subscriptions report
    with target_sat.ui_session() as session:
        session.reporttemplate.schedule(
            'Subscription - General Report',
            values={
                'output_format': 'JSON',
                'generate_at': '1970-01-01 17:10:00',
                'email': True,
                'email_to': 'root@localhost',
            },
        )
    randstring = gen_string('alpha')
    file_path = PurePath('/tmp/').joinpath(f'{randstring}.json')
    gzip_path = PurePath(f'{file_path}.gz')
    local_file = robottelo_tmp_dir.joinpath(f'{randstring}.json')
    local_gzip_file = Path(f'{local_file}.gz')
    expect_script = (
        f'#!/usr/bin/env expect\n'
        f'spawn mail\n'
        f'expect "& "\n'
        f'send "w $ /dev/null\\r"\n'
        f'expect "Enter filename"\n'
        f'send "\\r"\n'
        f'expect "Enter filename"\n'
        f'send "\\r"\n'
        f'expect "Enter filename"\n'
        f'send "\\025{gzip_path}\\r"\n'
        f'expect "&"\n'
        f'send "q\\r"\n'
    )

    assert target_sat.execute(f"expect -c '{expect_script}'").status == 0
    target_sat.get(remote_path=str(gzip_path), local_path=str(local_gzip_file))
    assert os.system(f'gunzip {local_gzip_file}') == 0
    data = json.loads(local_file.read_text())
    subscription_search = target_sat.api.Subscription(organization=module_sca_manifest_org).search()
    assert len(data) >= len(subscription_search) > 0
    keys_expected = [
        'Account number',
        'Available',
        'Contract number',
        'Days Remaining',
        'End date',
        'ID',
        'Name',
        'Organization',
        'Product Host Count',
        'Quantity',
        'SKU',
        'Start date',
    ]
    for subscription in data:
        assert sorted(list(subscription.keys())) == keys_expected


@pytest.mark.stubbed
def test_negative_bad_email(session):
    """Generate a report and request the result be sent to
        a wrong formatted e-mail address

    :id: cd19b90d-836f-4efd-c4bc-d5e09a909a67
    :setup: User with reporting access rights, some Host, some report with host input
    :steps:
        1. Monitor -> Report Templates
        2. Host - Registered Content Hosts -> Generate
        3. Check that the result should be sent via e-mail
        4. Submit
    :expectedresults: Error message about wrong e-mail address, no task is triggered
    :CaseImportance: Medium
    """


@pytest.mark.stubbed
def test_negative_nonauthor_of_report_cant_download_it(session):
    """The resulting report should only be downloadable by
        the user that generated it. Check.

    :id: cd19b90d-836f-4efd-c6bc-d5e09a909a67
    :setup: Installed Satellite, user that can list running tasks
    :steps:
        1. Monitor -> Report Templates
        2. In the reports row, in Actions column, click Generate
        3. Submit
        4. Wait for dynflow
        5. As a different user, try to download the generated report
    :expectedresults: Report can't be downloaded. Error.

    :CaseImportance: High
    """


@pytest.mark.rhel_ver_list([7, 8, 9])
def test_positive_generate_all_installed_packages_report(
    session, module_setup_content, rhel_contenthost, target_sat
):
    """Generate an report using the 'Host - All Installed Packages' Report template

    :id: 63ab3246-0fc5-48b3-ba56-7becfa0c5a7b

    :setup: Installed Satellite with Organization, Activation key,
            Content View, Content Host, and custom product with installed packages

    :steps:
        1. Monitor -> Report Templates
        2. Host - All Installed Packages -> Generate
        3. Select Date, Output format, and Hosts filter

    :expectedresults: A report is generated containing all installed package
            information for a host

    :BZ: 1826648

    :customerscenario: true
    """
    org, ak, cv, lce = module_setup_content
    target_sat.cli_factory.setup_org_for_a_custom_repo(
        {
            'url': settings.repos.yum_6.url,
            'organization-id': org.id,
            'content-view-id': cv.id,
            'lifecycle-environment-id': lce.id,
            'activationkey-id': ak.id,
        }
    )
    client = rhel_contenthost
    result = client.register(org, None, ak.name, target_sat)
    assert result.status == 0, f'Failed to register host: {result.stderr}'
    assert client.subscribed
    client.execute(f'yum -y install {FAKE_0_CUSTOM_PACKAGE_NAME} {FAKE_1_CUSTOM_PACKAGE}')
    with session:
        session.location.select('Default Location')
        result_html = session.reporttemplate.generate(
            'Host - All Installed Packages', values={'output_format': 'HTML'}
        )
    with open(result_html) as html_file:
        parser = etree.HTMLParser()
        tree = etree.parse(html_file, parser)
        tree_result = etree.tostring(tree.getroot(), pretty_print=True, method='html').decode()
    assert client.hostname in tree_result
    assert FAKE_1_CUSTOM_PACKAGE in tree_result


@pytest.mark.no_containers
@pytest.mark.rhel_ver_match(r'^(?!.*fips).*$')  # all versions, excluding any 'fips'
def test_positive_installable_errata_with_user(
    session, target_sat, function_org, function_lce, function_location, rhel_contenthost
):
    """Generate an Installable Errata report using the Report Template - Available Errata,
        with the option of 'Installable' with a registered user.

    :id: 036e3ed6-b31b-4481-b591-dae438e4e61d

    :setup: A Host with some applied errata

    :steps:
        1. Install an outdated package version
        2. Apply an errata which updates the package
        3. Downgrade the package impacted by the erratum
        4. Perform a search for any Available Errata
        5. Generate an Installable Report from the Available Errata with a registered user

    :expectedresults: A report is generated with the installable errata listed

    :CaseImportance: Medium

    :customerscenario: true

    :BZ: 1726504
    """
    activation_key = target_sat.api.ActivationKey(organization=function_org).create()
    custom_cv = target_sat.api.ContentView(organization=function_org).create()
    ERRATUM_ID = str(settings.repos.yum_6.errata[2])
    target_sat.cli_factory.setup_org_for_a_custom_repo(
        {
            'url': settings.repos.yum_6.url,
            'organization-id': function_org.id,
            'content-view-id': custom_cv.id,
            'lifecycle-environment-id': function_lce.id,
            'activationkey-id': activation_key.id,
        }
    )
    result = rhel_contenthost.register(
        function_org, function_location, activation_key.name, target_sat
    )
    assert f'The registered system name is: {rhel_contenthost.hostname}' in result.stdout
    assert rhel_contenthost.subscribed

    # Remove package if already installed on this host
    rhel_contenthost.execute(f'yum remove -y {FAKE_1_CUSTOM_PACKAGE_NAME}')
    # Install the outdated package version
    assert rhel_contenthost.execute(f'yum install -y {FAKE_1_CUSTOM_PACKAGE}').status == 0
    assert (
        rhel_contenthost.execute(f'rpm -q {FAKE_1_CUSTOM_PACKAGE_NAME}').stdout.strip()
        == FAKE_1_CUSTOM_PACKAGE
    )

    # Install/Apply the errata
    task_id = target_sat.api.JobInvocation().run(
        data={
            'feature': 'katello_errata_install',
            'inputs': {'errata': ERRATUM_ID},
            'targeting_type': 'static_query',
            'search_query': f'name = {rhel_contenthost.hostname}',
            'organization_id': function_org.id,
        },
    )['id']
    target_sat.wait_for_tasks(
        search_query=(f'label = Actions::RemoteExecution::RunHostsJob and id = {task_id}'),
        search_rate=15,
        max_tries=10,
    )
    # Check that applying erratum updated the package
    assert (
        rhel_contenthost.execute(f'rpm -q {FAKE_1_CUSTOM_PACKAGE_NAME}').stdout.strip()
        == FAKE_2_CUSTOM_PACKAGE
    )
    # Downgrade the package
    assert rhel_contenthost.execute(f'yum downgrade -y {FAKE_1_CUSTOM_PACKAGE}').status == 0
    # Generate the report
    with target_sat.ui_session() as session:
        session.organization.select(function_org.name)
        session.location.select(function_location.name)
        result_json = session.reporttemplate.generate(
            'Host - Available Errata',
            values={'output_format': 'JSON', 'installability': 'installable'},
        )
        with open(result_json) as json_file:
            data_json = json.load(json_file)
        assert ERRATUM_ID in data_json[0]['Erratum']
        assert FAKE_1_CUSTOM_PACKAGE_NAME in data_json[0]['Packages']
