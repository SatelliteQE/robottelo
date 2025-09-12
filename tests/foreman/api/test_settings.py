"""Test class for Setting Parameter values

:Requirement: Settings

:CaseAutomation: Automated

:CaseComponent: Settings

:Team: Endeavour

:CaseImportance: High

"""

import random

from fauxfactory import gen_string
import pytest
from requests.exceptions import HTTPError

from robottelo.constants import SUPPORTED_MIRRORING_POLICIES
from robottelo.utils.datafactory import (
    filtered_datapoint,
    generate_strings_list,
    parametrized,
    valid_data_list,
)


@filtered_datapoint
def valid_timeout_values():
    """Returns a list of valid values for sync connection timeout
    (min, max and random from the range)"""
    return ["0", "99999999", str(random.randint(1, 99999998))]


@pytest.mark.run_in_one_thread
@pytest.mark.upgrade
@pytest.mark.parametrize('setting_update', ['login_text'], indirect=True)
def test_positive_update_login_page_footer_text(setting_update):
    """Updates parameter "login_text" in settings

    :id: 91c5373d-b928-419d-8509-761adf5b94b0

    :CaseImportance: Critical

    :parametrized: yes

    :expectedresults: Parameter is updated successfully
    """
    login_text_value = random.choice(list(valid_data_list().values()))
    setting_update.value = login_text_value
    setting_update = setting_update.update({'value'})
    assert setting_update.value == login_text_value


@pytest.mark.run_in_one_thread
@pytest.mark.parametrize('setting_update', ['login_text'], indirect=True)
def test_positive_update_login_page_footer_text_without_value(setting_update):
    """Updates parameter "login_text" without any string (empty value)

    :id: 7a56f194-8bde-4dbf-9993-62eb6ab10733

    :parametrized: yes

    :expectedresults: login_text has empty value after update
    """
    setting_update.value = ""
    setting_update = setting_update.update({'value'})
    assert setting_update.value == ""


@pytest.mark.run_in_one_thread
@pytest.mark.parametrize('setting_update', ['login_text'], indirect=True)
def test_positive_update_login_page_footer_text_with_long_string(setting_update):
    """Attempt to update parameter "Login_page_footer_text"
        with long length string

    :id: fb8b0bf1-b475-435a-926b-861aa18d31f1

    :parametrized: yes

    :expectedresults: Parameter is updated
    """
    login_text_value = random.choice(list(generate_strings_list(1000)))
    setting_update.value = login_text_value
    setting_update = setting_update.update({'value'})
    assert setting_update.value == login_text_value


@pytest.mark.parametrize('setting_update', ['discovery_hostname'], indirect=True)
def test_negative_update_hostname_with_empty_fact(setting_update):
    """Update the Hostname_facts settings without any string(empty values)

    :id: b8e260fc-e263-4292-aa2f-ab37085c7758

    :parametrized: yes

    :expectedresults: Error should be raised on setting empty value for discovery_hostname
        setting
    """
    setting_update.value = ""
    with pytest.raises(HTTPError):
        setting_update.update({'value'})


@pytest.mark.parametrize('setting_update', ['discovery_prefix'], indirect=True)
def test_positive_update_hostname_prefix_without_value(setting_update):
    """Update the Hostname_prefix settings without any string(empty values)

    :id: 3867488c-d955-47af-ac0d-71f4016391d1

    :parametrized: yes

    :BZ: 1911228

    :expectedresults: Error should be raised on setting empty value for discovery_prefix setting
    """
    setting_update.value = ""
    with pytest.raises(HTTPError):
        setting_update.update({'value'})


@pytest.mark.parametrize('setting_update', ['discovery_prefix'], indirect=True)
def test_positive_update_hostname_default_prefix(setting_update):
    """Update the default set prefix of hostname_prefix setting

    :id: 4969994d-f934-4f0e-9a98-476b87eb0527

    :CaseImportance: Critical

    :parametrized: yes

    :expectedresults: Default set prefix should be updated with new value
    """
    discovery_prefix = random.choice(
        list(generate_strings_list(exclude_types=['alphanumeric', 'numeric']))
    )
    setting_update.value = discovery_prefix
    setting_update = setting_update.update({'value'})
    assert setting_update.value == discovery_prefix


@pytest.mark.stubbed
def test_positive_update_hostname_default_facts():
    """Update the default set fact of hostname_facts setting with list of
    facts like: bios_vendor,uuid

    :id: aa60d383-d193-4983-a8d7-3994e60a064b

    :expectedresults: Default set fact should be updated with facts list.

    :CaseAutomation: NotAutomated
    """


@pytest.mark.parametrize('setting_update', ['discovery_prefix'], indirect=True)
def test_negative_discover_host_with_invalid_prefix(setting_update):
    """Update the hostname_prefix with invalid string like
    -mac, 1mac or ^%$

    :id: 51091ed2-b0a2-433c-bcef-c8b4a3a34a05

    :parametrized: yes

    :verifies: SAT-37365

    :expectedresults: Validation error should be raised on updating
        hostname_prefix with invalid string, should start w/ letter

    """
    invalid_prefix = gen_string('numeric')
    setting_update.value = invalid_prefix
    with pytest.raises(HTTPError):
        setting_update.update({'value'})


@pytest.mark.run_in_one_thread
@pytest.mark.parametrize('download_policy', ["immediate", "on_demand"])
@pytest.mark.parametrize('setting_update', ['default_download_policy'], indirect=True)
def test_positive_custom_repo_download_policy(setting_update, download_policy, target_sat):
    """Check the set custom repository download policy for newly created custom repository.

    :id: d5150cce-ba85-4ea0-a8d1-6a54d0d29571

    :steps:
        1. Create a product, Organization
        2. Update the Default Custom Repository download policy in the setting.
        3. Create a custom repo under the created organization.
        4. Check the set policy of new created repository.
        5. Repeat steps 2 to 4 for both download policy.

    :parametrized: yes

    :expectedresults: The set download policy should be the default policy in the newly created
     repository.

    :CaseImportance: Medium
    """
    org = target_sat.api.Organization().create()
    prod = target_sat.api.Product(organization=org).create()
    setting_update.value = download_policy
    setting_update.update({'value'})
    repo = target_sat.api.Repository(product=prod, content_type='yum', organization=org).create()
    assert repo.download_policy == download_policy
    repo.delete()
    prod.delete()


@pytest.mark.run_in_one_thread
@pytest.mark.parametrize(
    ('content_type', 'mirroring_policy'),
    [
        (content_type, mirroring_policy)
        for content_type, policies in SUPPORTED_MIRRORING_POLICIES.items()
        for mirroring_policy in policies
    ],
)
def test_positive_custom_default_repo_mirroring_policy(
    request, content_type, mirroring_policy, module_product, module_target_sat
):
    """Verify that repositories are created with the correct mirroring policy
    for both YUM and non-YUM content types when the default setting is changed.

    :id: 6f8d2345-6789-4bcd-9012-3456789abcef

    :steps:
        1. Update the default custom repository mirroring policy setting.
        2. Create a custom repo.
        3. Check the mirroring policy of new created repository.

    :parametrized: yes

    :expectedresults: Repository is created with the specified mirroring policy
    """
    # Determine which setting to use based on content type
    if content_type == 'yum':
        setting_name = 'default_yum_mirroring_policy'
    else:
        setting_name = 'default_non_yum_mirroring_policy'

    # Get the current setting value and update it BEFORE creating the repository
    setting = module_target_sat.api.Setting().search(query={'search': f'name={setting_name}'})[0]
    original_value = setting.value
    setting.value = mirroring_policy
    setting.update(['value'])

    def restore_setting():
        setting.value = original_value
        setting.update(['value'])

    request.addfinalizer(restore_setting)

    repo = module_target_sat.api.Repository(
        product=module_product, content_type=content_type, organization=module_product.organization
    ).create()

    request.addfinalizer(repo.delete)

    assert repo.mirroring_policy == mirroring_policy


@pytest.mark.parametrize('valid_value', **parametrized(valid_timeout_values()))
@pytest.mark.parametrize('setting_update', ['sync_connect_timeout_v2'], indirect=True)
def test_positive_update_sync_timeout(setting_update, valid_value):
    """Check that values from provided range can be set to
    sync connection timeout

    :id: e25cd07b-a4a7-4ad3-9053-ad0bbaffbab7

    :CaseImportance: Medium

    :parametrized: yes

    :expectedresults: Default timeout should be updated with new value
    """
    setting_update.value = valid_value
    setting_update.update({'value'})
    setting_update = setting_update.read()
    assert str(setting_update.value) == valid_value


@pytest.mark.parametrize('invalid_value', ["-1", "3.1415", "2.71828e+11", "123456789", "0x3f77"])
@pytest.mark.parametrize('setting_update', ['sync_connect_timeout_v2'], indirect=True)
def test_negative_update_sync_timeout(setting_update, invalid_value):
    """Check that non-integer or too long values can't be set to
    sync connection timeout

    :id: 2c0dbb58-4a0c-4be1-9cd6-0c6cb17cc5c5

    :CaseImportance: Medium

    :parametrized: yes

    :expectedresults: Timeout shouldn't be updated with invalid value
    """
    setting_update.value = invalid_value
    with pytest.raises(HTTPError):
        setting_update.update({'value'})
