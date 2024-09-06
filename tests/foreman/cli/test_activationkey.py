"""Test class for Activation key CLI

:Requirement: Activationkey

:CaseAutomation: Automated

:CaseComponent: ActivationKeys

:team: Phoenix-subscriptions

:CaseImportance: High

"""

from fauxfactory import gen_alphanumeric, gen_string
import pytest

from robottelo.cli.defaults import Defaults
from robottelo.config import settings
from robottelo.constants import DEFAULT_ARCHITECTURE, PRDS, REPOS, REPOSET
from robottelo.exceptions import CLIFactoryError, CLIReturnCodeError
from robottelo.utils.datafactory import (
    invalid_values_list,
    parametrized,
    valid_data_list,
)


@pytest.fixture(scope='module')
def get_default_env(module_org, module_target_sat):
    """Get default lifecycle environment"""
    return module_target_sat.cli.LifecycleEnvironment.info(
        {'organization-id': module_org.id, 'name': 'Library'}
    )


@pytest.mark.tier1
@pytest.mark.parametrize('name', **parametrized(valid_data_list()))
def test_positive_create_with_name(module_target_sat, module_sca_manifest_org, name):
    """Create Activation key for all variations of Activation key
    name

    :id: a5aaab5e-bc18-459e-a384-74aef752ec88

    :expectedresults: Activation key is created with chosen name

    :CaseImportance: Critical

    :parametrized: yes
    """
    new_ak = module_target_sat.cli_factory.make_activation_key(
        {'organization-id': module_sca_manifest_org.id, 'name': name}
    )
    assert new_ak['name'] == name


@pytest.mark.tier1
@pytest.mark.parametrize('desc', **parametrized(valid_data_list()))
def test_positive_create_with_description(desc, module_org, module_target_sat):
    """Create Activation key for all variations of Description

    :id: 5a5ca7f9-1449-4365-ac8a-978605620bf2

    :expectedresults: Activation key is created with chosen description

    :CaseImportance: Critical

    :parametrized: yes
    """
    new_ak = module_target_sat.cli_factory.make_activation_key(
        {'organization-id': module_org.id, 'description': desc}
    )
    assert new_ak['description'] == desc


@pytest.mark.tier1
def test_positive_create_with_default_lce_by_id(module_org, get_default_env, target_sat):
    """Create Activation key with associated default environment

    :id: 9171adb2-c9ac-4cda-978f-776826668aa3

    :expectedresults: Activation key is created and associated to Library

    :CaseImportance: Critical
    """
    lce = get_default_env
    new_ak_env = target_sat.cli_factory.make_activation_key(
        {'organization-id': module_org.id, 'lifecycle-environment-id': lce['id']}
    )
    assert new_ak_env['lifecycle-environment'] == lce['name']


@pytest.mark.tier1
def test_positive_create_with_non_default_lce(module_org, module_target_sat):
    """Create Activation key with associated custom environment

    :id: ad4d4611-3fb5-4449-ae47-305f9931350e

    :expectedresults: Activation key is created and associated to expected
        environment

    :CaseImportance: Critical
    """
    env = module_target_sat.cli_factory.make_lifecycle_environment(
        {'organization-id': module_org.id}
    )
    new_ak_env = module_target_sat.cli_factory.make_activation_key(
        {'organization-id': module_org.id, 'lifecycle-environment-id': env['id']}
    )
    assert new_ak_env['lifecycle-environment'] == env['name']


@pytest.mark.tier1
def test_positive_create_with_default_lce_by_name(module_org, get_default_env, module_target_sat):
    """Create Activation key with associated environment by name

    :id: 7410f7c4-e8b5-4080-b6d2-65dbcedffe8a

    :expectedresults: Activation key is created

    :CaseImportance: Critical
    """
    lce = get_default_env
    new_ak_env = module_target_sat.cli_factory.make_activation_key(
        {'organization-id': module_org.id, 'lifecycle-environment': lce['name']}
    )
    assert new_ak_env['lifecycle-environment'] == lce['name']


@pytest.mark.tier2
@pytest.mark.parametrize('name', **parametrized(valid_data_list()))
def test_positive_create_with_cv(name, module_org, get_default_env, module_target_sat):
    """Create Activation key for all variations of Content Views

    :id: ec7b1af5-c3f4-40c3-b1df-c69c02a3b9a7

    :expectedresults: Activation key is created and has proper content view
        assigned

    :parametrized: yes
    """
    new_cv = module_target_sat.cli_factory.make_content_view(
        {'name': name, 'organization-id': module_org.id}
    )
    module_target_sat.cli.ContentView.publish({'id': new_cv['id']})
    new_ak_cv = module_target_sat.cli_factory.make_activation_key(
        {
            'content-view': new_cv['name'],
            'lifecycle-environment': get_default_env['name'],
            'organization-id': module_org.id,
        }
    )
    assert new_ak_cv['content-view'] == name


@pytest.mark.tier1
def test_positive_create_with_usage_limit_default(module_org, module_target_sat):
    """Create Activation key with default Usage limit (Unlimited)

    :id: cba13c72-9845-486d-beff-e0fb55bb762c

    :expectedresults: Activation key is created

    :CaseImportance: Critical
    """
    new_ak = module_target_sat.cli_factory.make_activation_key({'organization-id': module_org.id})
    assert new_ak['host-limit'] == '0 of Unlimited'


@pytest.mark.tier1
def test_positive_create_with_usage_limit_finite(module_org, module_target_sat):
    """Create Activation key with finite Usage limit

    :id: 529a0f9e-977f-4e9d-a1af-88bb98c28a6a

    :expectedresults: Activation key is created

    :CaseImportance: Critical
    """
    new_ak = module_target_sat.cli_factory.make_activation_key(
        {'organization-id': module_org.id, 'max-hosts': '10'}
    )
    assert new_ak['host-limit'] == '0 of 10'


@pytest.mark.tier2
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_create_content_and_check_enabled(module_org, module_target_sat):
    """Create activation key and add content to it. Check enabled state.

    :id: abfc6c6e-acd1-4761-b309-7e68e1d17172

    :expectedresults: Enabled state is shown for product content
        successfully

    :BZ: 1361993
    """
    result = module_target_sat.cli_factory.setup_org_for_a_custom_repo(
        {'url': settings.repos.yum_0.url, 'organization-id': module_org.id}
    )
    content = module_target_sat.cli.ActivationKey.product_content(
        {'id': result['activationkey-id'], 'organization-id': module_org.id}
    )
    assert content[0]['default-enabled?'] == 'false'


@pytest.mark.tier2
@pytest.mark.parametrize('name', **parametrized(invalid_values_list()))
def test_negative_create_with_invalid_name(name, module_org, module_target_sat):
    """Create Activation key with invalid Name

    :id: d9b7e3a9-1d24-4e47-bd4a-dce75772d829

    :expectedresults: Activation key is not created. Appropriate error
        shown.

    :CaseImportance: Low

    :parametrized: yes
    """
    with pytest.raises(CLIFactoryError) as raise_ctx:
        module_target_sat.cli_factory.make_activation_key(
            {'organization-id': module_org.id, 'name': name}
        )
    if name in ['', ' ', '\t']:
        assert 'Name must contain at least 1 character' in str(raise_ctx)
    if len(name) > 255:
        assert 'Name is too long (maximum is 255 characters)' in str(raise_ctx)


@pytest.mark.tier3
@pytest.mark.parametrize(
    'limit',
    **parametrized([value for value in invalid_values_list() if not value.isdigit()] + [0.5]),
)
def test_negative_create_with_usage_limit_with_not_integers(module_org, limit, module_target_sat):
    """Create Activation key with non integers Usage Limit

    :id: 247ebc2e-c80f-488b-aeaf-6bf5eba55375

    :expectedresults: Activation key is not created. Appropriate error
        shown.

    :CaseImportance: Low

    :parametrized: yes
    """
    # exclude numeric values from invalid values list
    # invalid_values = [value for value in invalid_values_list() if not value.isdigit()]
    # invalid_values.append(0.5)
    with pytest.raises(CLIFactoryError) as raise_ctx:
        module_target_sat.cli_factory.make_activation_key(
            {'organization-id': module_org.id, 'max-hosts': limit}
        )
    if isinstance(limit, int) and limit < 1:
        assert 'Max hosts cannot be less than one' in str(raise_ctx)
    if isinstance(limit, str):
        assert 'Numeric value is required.' in str(raise_ctx)


@pytest.mark.tier3
@pytest.mark.parametrize('invalid_values', ['-1', '-500', 0])
def test_negative_create_with_usage_limit_with_invalid_integers(
    module_org, invalid_values, module_target_sat
):
    """Create Activation key with invalid integers Usage Limit

    :id: 9089f756-fda8-4e28-855c-cf8273f7c6cd

    :expectedresults: Activation key is not created. Appropriate error
        shown.

    :CaseImportance: Low

    :parametrized: yes
    """
    with pytest.raises(CLIFactoryError) as raise_ctx:
        module_target_sat.cli_factory.make_activation_key(
            {'organization-id': module_org.id, 'max-hosts': invalid_values}
        )
    assert 'Failed to create ActivationKey with data:' in str(raise_ctx)


@pytest.mark.tier1
@pytest.mark.parametrize('name', **parametrized(valid_data_list()))
def test_positive_delete_by_name(name, module_org, module_target_sat):
    """Create Activation key and delete it for all variations of
    Activation key name

    :id: ef5f6a28-6bfd-415b-aac9-b3dc9a014ca9

    :expectedresults: Activation key is deleted

    :CaseImportance: High

    :parametrized: yes
    """
    new_ak = module_target_sat.cli_factory.make_activation_key(
        {'name': name, 'organization-id': module_org.id}
    )
    module_target_sat.cli.ActivationKey.delete(
        {'name': new_ak['name'], 'organization-id': module_org.id}
    )
    with pytest.raises(CLIReturnCodeError):
        module_target_sat.cli.ActivationKey.info({'id': new_ak['id']})


@pytest.mark.tier1
def test_positive_delete_by_org_name(module_org, module_target_sat):
    """Create Activation key and delete it using organization name
    for which that key was created

    :id: 006cbe5c-fb72-43a1-9760-30c97043c36b

    :expectedresults: Activation key is deleted

    :CaseImportance: High
    """
    new_ak = module_target_sat.cli_factory.make_activation_key({'organization-id': module_org.id})
    module_target_sat.cli.ActivationKey.delete(
        {'name': new_ak['name'], 'organization-id': module_org.id}
    )
    with pytest.raises(CLIReturnCodeError):
        module_target_sat.cli.ActivationKey.info({'id': new_ak['id']})


@pytest.mark.tier1
def test_positive_delete_by_org_label(module_org, module_target_sat):
    """Create Activation key and delete it using organization label
    for which that key was created

    :id: f66e5a42-b531-4290-a907-9f5c01305885

    :expectedresults: Activation key is deleted

    :CaseImportance: High
    """
    new_ak = module_target_sat.cli_factory.make_activation_key({'organization-id': module_org.id})
    module_target_sat.cli.ActivationKey.delete(
        {'name': new_ak['name'], 'organization-label': module_org.label}
    )
    with pytest.raises(CLIReturnCodeError):
        module_target_sat.cli.ActivationKey.info({'id': new_ak['id']})


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_delete_with_cv(module_org, module_target_sat):
    """Create activation key with content view assigned to it and
    delete it using activation key id

    :id: bba323fa-0362-4a9b-97af-560d446cbb6c

    :expectedresults: Activation key is deleted
    """
    new_cv = module_target_sat.cli_factory.make_content_view({'organization-id': module_org.id})
    new_ak = module_target_sat.cli_factory.make_activation_key(
        {'organization-id': module_org.id, 'content-view': new_cv['name']}
    )
    module_target_sat.cli.ActivationKey.delete({'id': new_ak['id']})
    with pytest.raises(CLIReturnCodeError):
        module_target_sat.cli.ActivationKey.info({'id': new_ak['id']})


@pytest.mark.tier2
def test_positive_delete_with_lce(module_org, get_default_env, module_target_sat):
    """Create activation key with lifecycle environment assigned to
    it and delete it using activation key id

    :id: e1830e52-5b1a-4ac4-8d0a-df6efb218a8b

    :expectedresults: Activation key is deleted
    """
    new_ak = module_target_sat.cli_factory.make_activation_key(
        {'organization-id': module_org.id, 'lifecycle-environment': get_default_env['name']}
    )
    module_target_sat.cli.ActivationKey.delete({'id': new_ak['id']})
    with pytest.raises(CLIReturnCodeError):
        module_target_sat.cli.ActivationKey.info({'id': new_ak['id']})


@pytest.mark.tier1
@pytest.mark.parametrize('name', **parametrized(valid_data_list()))
def test_positive_update_name_by_id(module_org, name, module_target_sat):
    """Update Activation Key Name in Activation key searching by ID

    :id: bc304894-fd9b-4622-96e3-57c2257e26ca

    :expectedresults: Activation key is updated

    :CaseImportance: Critical

    :parametrized: yes
    """
    activation_key = module_target_sat.cli_factory.make_activation_key(
        {'organization-id': module_org.id}
    )
    module_target_sat.cli.ActivationKey.update(
        {'id': activation_key['id'], 'new-name': name, 'organization-id': module_org.id}
    )
    updated_ak = module_target_sat.cli.ActivationKey.info({'id': activation_key['id']})
    assert updated_ak['name'] == name


@pytest.mark.tier1
def test_positive_update_name_by_name(module_org, module_target_sat):
    """Update Activation Key Name in an Activation key searching by
    name

    :id: bce4533e-1a58-4edb-a51a-4aa46bc28676

    :expectedresults: Activation key is updated

    :CaseImportance: Critical
    """
    new_name = gen_string('alpha')
    activation_key = module_target_sat.cli_factory.make_activation_key(
        {'organization-id': module_org.id}
    )
    module_target_sat.cli.ActivationKey.update(
        {'name': activation_key['name'], 'new-name': new_name, 'organization-id': module_org.id}
    )
    updated_ak = module_target_sat.cli.ActivationKey.info({'id': activation_key['id']})
    assert updated_ak['name'] == new_name


@pytest.mark.tier1
@pytest.mark.parametrize('description', **parametrized(valid_data_list()))
def test_positive_update_description(description, module_org, module_target_sat):
    """Update Description in an Activation key

    :id: 60a4e860-d99c-431e-b70b-9b0fa90d839b

    :expectedresults: Activation key is updated

    :CaseImportance: High

    :parametrized: yes
    """
    activation_key = module_target_sat.cli_factory.make_activation_key(
        {'organization-id': module_org.id}
    )
    module_target_sat.cli.ActivationKey.update(
        {
            'description': description,
            'name': activation_key['name'],
            'organization-id': module_org.id,
        }
    )
    updated_ak = module_target_sat.cli.ActivationKey.info({'id': activation_key['id']})
    assert updated_ak['description'] == description


@pytest.mark.tier2
def test_positive_update_lce(module_org, get_default_env, module_target_sat):
    """Update Environment in an Activation key

    :id: 55aaee60-b8c8-49f0-995a-6c526b9b653b

    :expectedresults: Activation key is updated
    """
    ak_env = module_target_sat.cli_factory.make_activation_key(
        {'organization-id': module_org.id, 'lifecycle-environment-id': get_default_env['id']}
    )
    env = module_target_sat.cli_factory.make_lifecycle_environment(
        {'organization-id': module_org.id}
    )
    new_cv = module_target_sat.cli_factory.make_content_view({'organization-id': module_org.id})
    module_target_sat.cli.ContentView.publish({'id': new_cv['id']})
    cvv = module_target_sat.cli.ContentView.info({'id': new_cv['id']})['versions'][0]
    module_target_sat.cli.ContentView.version_promote(
        {'id': cvv['id'], 'to-lifecycle-environment-id': env['id']}
    )
    module_target_sat.cli.ActivationKey.update(
        {
            'id': ak_env['id'],
            'lifecycle-environment-id': env['id'],
            'content-view': new_cv['name'],
            'organization-id': module_org.id,
        }
    )
    updated_ak = module_target_sat.cli.ActivationKey.info({'id': ak_env['id']})
    assert updated_ak['lifecycle-environment'] == env['name']


@pytest.mark.tier2
def test_positive_update_cv(module_org, module_target_sat):
    """Update Content View in an Activation key

    :id: aa94997d-fc9b-4532-aeeb-9f27b9834914

    :expectedresults: Activation key is updated
    """
    cv = module_target_sat.cli_factory.make_content_view({'organization-id': module_org.id})
    ak_cv = module_target_sat.cli_factory.make_activation_key(
        {'organization-id': module_org.id, 'content-view-id': cv['id']}
    )
    new_cv = module_target_sat.cli_factory.make_content_view({'organization-id': module_org.id})
    module_target_sat.cli.ActivationKey.update(
        {'content-view': new_cv['name'], 'name': ak_cv['name'], 'organization-id': module_org.id}
    )
    updated_ak = module_target_sat.cli.ActivationKey.info({'id': ak_cv['id']})
    assert updated_ak['content-view'] == new_cv['name']


@pytest.mark.tier1
def test_positive_update_usage_limit_to_finite_number(module_org, module_target_sat):
    """Update Usage limit from Unlimited to a finite number

    :id: a55bb8dc-c7d8-4a6a-ac0f-1d5a377da543

    :expectedresults: Activation key is updated

    :CaseImportance: Critical
    """
    new_ak = module_target_sat.cli_factory.make_activation_key({'organization-id': module_org.id})
    assert new_ak['host-limit'] == '0 of Unlimited'
    module_target_sat.cli.ActivationKey.update(
        {'max-hosts': '2147483647', 'name': new_ak['name'], 'organization-id': module_org.id}
    )
    updated_ak = module_target_sat.cli.ActivationKey.info({'id': new_ak['id']})
    assert updated_ak['host-limit'] == '0 of 2147483647'


@pytest.mark.tier1
def test_positive_update_usage_limit_to_unlimited(module_org, module_target_sat):
    """Update Usage limit from definite number to Unlimited

    :id: 0b83657b-41d1-4fb2-9c23-c36011322b83

    :expectedresults: Activation key is updated

    :CaseImportance: Critical
    """
    new_ak = module_target_sat.cli_factory.make_activation_key(
        {'organization-id': module_org.id, 'max-hosts': '10'}
    )
    assert new_ak['host-limit'] == '0 of 10'
    module_target_sat.cli.ActivationKey.update(
        {'unlimited-hosts': True, 'name': new_ak['name'], 'organization-id': module_org.id}
    )
    updated_ak = module_target_sat.cli.ActivationKey.info({'id': new_ak['id']})
    assert updated_ak['host-limit'] == '0 of Unlimited'


@pytest.mark.tier2
@pytest.mark.parametrize('name', **parametrized(invalid_values_list()))
def test_negative_update_name(module_org, name, module_target_sat):
    """Try to update Activation Key using invalid value for its name

    :id: b75e7c38-fde2-4110-ba65-4157319fc159

    :expectedresults: Activation key is not updated. Appropriate error
        shown.

    :CaseImportance: Low

    :parametrized: yes
    """
    new_ak = module_target_sat.cli_factory.make_activation_key({'organization-id': module_org.id})
    with pytest.raises(CLIReturnCodeError) as raise_ctx:
        module_target_sat.cli.ActivationKey.update(
            {'id': new_ak['id'], 'new-name': name, 'organization-id': module_org.id}
        )
    assert 'Could not update the activation key:' in raise_ctx.value.message


@pytest.mark.tier2
def test_negative_update_usage_limit(module_org, module_target_sat):
    """Try to update Activation Key using invalid value for its
    usage limit attribute

    :id: cb5fa263-924c-471f-9c57-9506117ca92d

    :expectedresults: Activation key is not updated. Appropriate error
        shown.

    :CaseImportance: Low
    """
    new_ak = module_target_sat.cli_factory.make_activation_key({'organization-id': module_org.id})
    with pytest.raises(CLIReturnCodeError) as raise_ctx:
        module_target_sat.cli.ActivationKey.update(
            {'max-hosts': int('9' * 20), 'id': new_ak['id'], 'organization-id': module_org.id}
        )
    assert 'Validation failed: Max hosts must be less than 2147483648' in raise_ctx.value.message


@pytest.mark.tier3
@pytest.mark.upgrade
@pytest.mark.rhel_ver_list([settings.content_host.default_rhel_version])
def test_positive_usage_limit(module_org, module_location, target_sat, content_hosts):
    """Test that Usage limit actually limits usage

    :id: 00ded856-e939-4140-ac84-91b6a8643623

    :steps:

        1. Create Activation key
        2. Update Usage Limit to a finite number
        3. Register Content hosts to match the Usage Limit
        4. Attempt to register an other Content host after reaching the
           Usage Limit

    :expectedresults: Content host Registration fails. Appropriate error
        shown

    :CaseImportance: Critical
    """
    max_hosts = 1
    env = target_sat.cli_factory.make_lifecycle_environment({'organization-id': module_org.id})
    new_cv = target_sat.cli_factory.make_content_view({'organization-id': module_org.id})
    target_sat.cli.ContentView.publish({'id': new_cv['id']})
    cvv = target_sat.cli.ContentView.info({'id': new_cv['id']})['versions'][0]
    target_sat.cli.ContentView.version_promote(
        {'id': cvv['id'], 'to-lifecycle-environment-id': env['id']}
    )
    new_ak = target_sat.cli_factory.make_activation_key(
        {
            'lifecycle-environment-id': env['id'],
            'content-view': new_cv['name'],
            'organization-id': module_org.id,
            'max-hosts': max_hosts,
        }
    )
    vm1, vm2 = content_hosts
    vm1.register(module_org, module_location, new_ak['name'], target_sat)
    assert vm1.subscribed
    result = vm2.register(module_org, module_location, new_ak['name'], target_sat)
    assert not vm2.subscribed
    assert result.status, 'Second registration was expected to fail'
    assert f"Max Hosts ({max_hosts}) reached for activation key '{new_ak.name}'" in result.stderr


@pytest.mark.tier2
@pytest.mark.parametrize('host_col_name', **parametrized(valid_data_list()))
def test_positive_update_host_collection(module_org, host_col_name, module_target_sat):
    """Test that host collections can be associated to Activation
    Keys

    :id: 2114132a-fede-4791-98e7-a463ad79f398

    :BZ: 1110476

    :expectedresults: Host collections are successfully associated to
        Activation key

    :parametrized: yes
    """
    activation_key = module_target_sat.cli_factory.make_activation_key(
        {'organization-id': module_org.id}
    )
    new_host_col_name = module_target_sat.cli_factory.make_host_collection(
        {'name': host_col_name, 'organization-id': module_org.id}
    )['name']
    # Assert that name matches data passed
    assert new_host_col_name == host_col_name
    module_target_sat.cli.ActivationKey.add_host_collection(
        {
            'host-collection': new_host_col_name,
            'name': activation_key['name'],
            'organization-id': module_org.id,
        }
    )
    activation_key = module_target_sat.cli.ActivationKey.info({'id': activation_key['id']})
    assert activation_key['host-collections'][0]['name'] == host_col_name


@pytest.mark.run_in_one_thread
@pytest.mark.tier2
def test_positive_update_host_collection_with_default_org(module_org, module_target_sat):
    """Test that host collection can be associated to Activation
    Keys with specified default organization setting in config

    :id: 01e830e9-91fd-4e45-9aaf-862e1fe134df

    :expectedresults: Host collection is successfully associated to
        Activation key

    :BZ: 1364876
    """
    Defaults.add({'param-name': 'organization_id', 'param-value': module_org.id})
    try:
        activation_key = module_target_sat.cli_factory.make_activation_key(
            {'organization-id': module_org.id}
        )
        host_col = module_target_sat.cli_factory.make_host_collection()
        module_target_sat.cli.ActivationKey.add_host_collection(
            {'host-collection': host_col['name'], 'name': activation_key['name']}
        )
        activation_key = module_target_sat.cli.ActivationKey.info({'id': activation_key['id']})
        assert activation_key['host-collections'][0]['name'] == host_col['name']
    finally:
        Defaults.delete({'param-name': 'organization_id'})


@pytest.mark.run_in_one_thread
@pytest.mark.tier3
def test_positive_add_redhat_product(function_sca_manifest_org, target_sat):
    """Test that RH product can be associated to Activation Keys

    :id: 7b15de8e-edde-41aa-937b-ad6aa529891a

    :expectedresults: RH products are successfully associated to Activation
        key
    """
    org = function_sca_manifest_org

    # Using CDN as we need this repo to be RH one no matter are we in
    # downstream or cdn
    result = target_sat.cli_factory.setup_org_for_a_rh_repo(
        {
            'product': PRDS['rhel'],
            'repository-set': REPOSET['rhst7'],
            'repository': REPOS['rhst7']['name'],
            'organization-id': org.id,
        },
        force_use_cdn=True,
    )
    content = target_sat.cli.ActivationKey.product_content(
        {'id': result['activationkey-id'], 'organization-id': org.id}
    )
    assert content[0]['name'] == REPOSET['rhst7']


@pytest.mark.tier3
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_add_custom_product(function_org, target_sat):
    """Test that custom product can be associated to Activation Keys

    :id: 96ace967-e165-4069-8ff7-f54c4c822de0

    :expectedresults: Custom products are successfully associated to
        Activation key

    :BZ: 1426386
    """
    result = target_sat.cli_factory.setup_org_for_a_custom_repo(
        {'url': settings.repos.yum_0.url, 'organization-id': function_org.id}
    )
    repo = target_sat.cli.Repository.info({'id': result['repository-id']})
    content = target_sat.cli.ActivationKey.product_content(
        {'id': result['activationkey-id'], 'organization-id': function_org.id}
    )
    assert content[0]['name'] == repo['name']


@pytest.mark.run_in_one_thread
@pytest.mark.tier3
@pytest.mark.upgrade
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_add_redhat_and_custom_products(module_target_sat, function_sca_manifest_org):
    """Test if RH/Custom product can be associated to Activation key

    :id: 74c77426-18f5-4abb-bca9-a2135f7fcc1f

    :steps:

        1. Create Activation key
        2. Associate RH product(s) to Activation Key
        3. Associate custom product(s) to Activation Key

    :expectedresults: RH/Custom product is successfully associated to
        Activation key

    :BZ: 1426386
    """
    org = function_sca_manifest_org
    # Using CDN as we need this repo to be RH one no matter are we in
    # downstream or cdn
    result = module_target_sat.cli_factory.setup_org_for_a_rh_repo(
        {
            'product': PRDS['rhel'],
            'repository-set': REPOSET['rhst7'],
            'repository': REPOS['rhst7']['name'],
            'organization-id': org.id,
        },
        force_use_cdn=True,
    )
    result = module_target_sat.cli_factory.setup_org_for_a_custom_repo(
        {
            'url': settings.repos.yum_0.url,
            'organization-id': org.id,
            'activationkey-id': result['activationkey-id'],
            'content-view-id': result['content-view-id'],
            'lifecycle-environment-id': result['lifecycle-environment-id'],
        }
    )
    repo = module_target_sat.cli.Repository.info({'id': result['repository-id']})
    content = module_target_sat.cli.ActivationKey.product_content(
        {'id': result['activationkey-id'], 'organization-id': org.id}
    )
    assert len(content) == 2
    assert {REPOSET['rhst7'], repo['name']} == {pc['name'] for pc in content}


@pytest.mark.tier3
@pytest.mark.upgrade
@pytest.mark.rhel_ver_match('[^6]')
def test_positive_update_aks_to_chost(
    module_org, module_location, rhel_contenthost, module_target_sat
):
    """Check if multiple Activation keys can be attached to a Content host

    :id: 24fddd9c-03ae-41a7-8649-72296cbbafdf

    :expectedresults: Multiple Activation keys are attached to a Content host

    :parametrized: yes
    """
    env = module_target_sat.cli_factory.make_lifecycle_environment(
        {'organization-id': module_org.id}
    )
    new_cv = module_target_sat.cli_factory.make_content_view({'organization-id': module_org.id})
    module_target_sat.cli.ContentView.publish({'id': new_cv['id']})
    cvv = module_target_sat.cli.ContentView.info({'id': new_cv['id']})['versions'][0]
    module_target_sat.cli.ContentView.version_promote(
        {'id': cvv['id'], 'to-lifecycle-environment-id': env['id']}
    )
    new_aks = [
        module_target_sat.cli_factory.make_activation_key(
            {
                'lifecycle-environment-id': env['id'],
                'content-view': new_cv['name'],
                'organization-id': module_org.id,
            }
        )
        for _ in range(2)
    ]
    for ak in new_aks:
        rhel_contenthost.register(
            org=module_org,
            loc=module_location,
            activation_keys=ak['name'],
            target=module_target_sat,
        )
        assert rhel_contenthost.subscribed


@pytest.mark.stubbed
@pytest.mark.tier3
def test_positive_update_aks_to_chost_in_one_command(module_org):
    """Check if multiple Activation keys can be attached to a
    Content host in one command. Here is a command details

    subscription-manager register --help

    ...

    --activationkey=ACTIVATION_KEYS activation key to use for registration
    (can be specified more than once)

    ...

    This means that we can re-use `--activationkey` option more than once
    to add different keys

    :id: 888669e2-2ff7-48e3-9c56-6ac497bec5a0

    :expectedresults: Multiple Activation keys are attached to a Content
        host
    """


@pytest.mark.tier1
@pytest.mark.parametrize('name', **parametrized(valid_data_list()))
def test_positive_list_by_name(module_org, name, module_target_sat):
    """List Activation key for all variations of Activation key name

    :id: 644b70d9-86c1-4e26-b38e-6aafab3efa34

    :expectedresults: Activation key is listed

    :CaseImportance: Critical

    :parametrized: yes
    """
    module_target_sat.cli_factory.make_activation_key(
        {'organization-id': module_org.id, 'name': name}
    )
    result = module_target_sat.cli.ActivationKey.list(
        {'name': name, 'organization-id': module_org.id}
    )
    assert len(result) == 1
    assert result[0]['name'] == name


@pytest.mark.tier1
def test_positive_list_by_cv_id(module_org, module_target_sat):
    """List Activation key for provided Content View ID

    :id: 4d9aad38-cd6e-41cb-99a0-9a593cf22655

    :expectedresults: Activation key is listed

    :CaseImportance: High
    """
    cv = module_target_sat.cli_factory.make_content_view({'organization-id': module_org.id})
    module_target_sat.cli_factory.make_activation_key(
        {'organization-id': module_org.id, 'content-view-id': cv['id']}
    )
    result = module_target_sat.cli.ActivationKey.list(
        {'content-view-id': cv['id'], 'organization-id': module_org.id}
    )
    assert len(result) == 1
    assert result[0]['content-view'] == cv['name']


@pytest.mark.tier1
def test_positive_create_using_old_name(module_org, module_target_sat):
    """Create activation key, rename it and create another with the
    initial name

    :id: 9801319a-f42c-41a4-9ea4-3718e544c8e0

    :expectedresults: Activation key is created

    :CaseImportance: High
    """
    name = gen_string('utf8')
    activation_key = module_target_sat.cli_factory.make_activation_key(
        {'organization-id': module_org.id, 'name': name}
    )
    new_name = gen_string('utf8')
    module_target_sat.cli.ActivationKey.update(
        {'id': activation_key['id'], 'new-name': new_name, 'organization-id': module_org.id}
    )
    activation_key = module_target_sat.cli.ActivationKey.info({'id': activation_key['id']})
    assert activation_key['name'] == new_name
    new_activation_key = module_target_sat.cli_factory.make_activation_key(
        {'name': name, 'organization-id': module_org.id}
    )
    assert new_activation_key['name'] == name


@pytest.mark.tier2
def test_positive_remove_host_collection_by_id(module_org, module_target_sat):
    """Test that hosts associated to Activation Keys can be removed
    using id of that host collection

    :id: 20f8ecca-1756-4900-b966-f0144b6bd0aa

    :steps:

        1. Create Activation key
        2. Create host collection
        3. Associate host collection to Activation key
        4. Remove host collection associated to Activation key using id of
           that collection

    :expectedresults: Host collection successfully removed from activation
        key

    :CaseImportance: Medium

    :BZ: 1336716
    """
    activation_key = module_target_sat.cli_factory.make_activation_key(
        {'organization-id': module_org.id}
    )
    new_host_col = module_target_sat.cli_factory.make_host_collection(
        {'name': gen_string('alpha'), 'organization-id': module_org.id}
    )
    module_target_sat.cli.ActivationKey.add_host_collection(
        {
            'host-collection-id': new_host_col['id'],
            'name': activation_key['name'],
            'organization': module_org.name,
        }
    )
    activation_key = module_target_sat.cli.ActivationKey.info({'id': activation_key['id']})
    assert len(activation_key['host-collections']) == 1
    module_target_sat.cli.ActivationKey.remove_host_collection(
        {
            'host-collection-id': new_host_col['id'],
            'name': activation_key['name'],
            'organization': module_org.name,
        }
    )
    activation_key = module_target_sat.cli.ActivationKey.info({'id': activation_key['id']})
    assert len(activation_key['host-collections']) == 0


@pytest.mark.tier2
@pytest.mark.parametrize('host_col', **parametrized(valid_data_list()))
def test_positive_remove_host_collection_by_name(module_org, host_col, module_target_sat):
    """Test that hosts associated to Activation Keys can be removed
    using name of that host collection

    :id: 1a559a82-db5f-48b0-beeb-2fa02aed7ef9

    :steps:

        1. Create Activation key
        2. Create host collection
        3. Associate host collection to Activation key
        4. Remove the host collection associated to Activation key using
           name of that collection

    :expectedresults: Host collection successfully removed from activation
        key

    :BZ: 1336716

    :parametrized: yes
    """
    activation_key = module_target_sat.cli_factory.make_activation_key(
        {'organization-id': module_org.id}
    )
    new_host_col = module_target_sat.cli_factory.make_host_collection(
        {'name': host_col, 'organization-id': module_org.id}
    )
    # Assert that name matches data passed
    assert new_host_col['name'] == host_col
    module_target_sat.cli.ActivationKey.add_host_collection(
        {
            'host-collection': new_host_col['name'],
            'name': activation_key['name'],
            'organization-id': module_org.id,
        }
    )
    activation_key = module_target_sat.cli.ActivationKey.info({'id': activation_key['id']})
    assert len(activation_key['host-collections']) == 1
    assert activation_key['host-collections'][0]['name'] == host_col
    module_target_sat.cli.ActivationKey.remove_host_collection(
        {
            'host-collection': new_host_col['name'],
            'name': activation_key['name'],
            'organization-id': module_org.id,
        }
    )
    activation_key = module_target_sat.cli.ActivationKey.info({'id': activation_key['id']})
    assert len(activation_key['host-collections']) == 0


@pytest.mark.tier2
def test_create_ak_with_syspurpose_set(module_sca_manifest_org, module_target_sat):
    """Test that an activation key can be created with system purpose values set.

    :id: ac8931e5-7089-494a-adac-cee2a8ab57ee

    :steps:
        1. Create Activation key with system purpose values set
        2. Read Activation key values and assert system purpose values are set
        3. Clear AK system purpose values
        4. Read the AK system purpose values and assert system purpose values are unset

    :CaseImportance: Medium

    :BZ: 1789028
    """
    # Requires Cls org and manifest. Manifest is for self-support values.
    new_ak = module_target_sat.cli_factory.make_activation_key(
        {
            'purpose-addons': "test-addon1, test-addon2",
            'purpose-role': "test-role",
            'purpose-usage': "test-usage",
            'service-level': "Self-Support",
            'organization-id': module_sca_manifest_org.id,
        }
    )
    assert new_ak['system-purpose']['purpose-addons'] == "test-addon1, test-addon2"
    assert new_ak['system-purpose']['purpose-role'] == "test-role"
    assert new_ak['system-purpose']['purpose-usage'] == "test-usage"
    assert new_ak['system-purpose']['service-level'] == "Self-Support"
    # Check that system purpose values can be deleted.
    module_target_sat.cli.ActivationKey.update(
        {
            'id': new_ak['id'],
            'purpose-addons': '',
            'purpose-role': '',
            'purpose-usage': '',
            'service-level': '',
            'organization-id': module_sca_manifest_org.id,
        }
    )
    updated_ak = module_target_sat.cli.ActivationKey.info(
        {'id': new_ak['id'], 'organization-id': module_sca_manifest_org.id}
    )
    assert updated_ak['system-purpose']['purpose-addons'] == ''
    assert updated_ak['system-purpose']['purpose-role'] == ''
    assert updated_ak['system-purpose']['purpose-usage'] == ''


@pytest.mark.tier2
def test_update_ak_with_syspurpose_values(module_sca_manifest_org, module_target_sat):
    """Test that system purpose values can be added to an existing activation key
    and can then be changed.

    :id: db943c05-70f1-4385-9537-fe23368a9dfd

    :steps:

        1. Create Activation key with no system purpose values set
        2. Assert system purpose values are not set
        3. Add system purpose values
        4. Read the AK system purpose values and assert system purpose values are set
        5. Update the system purpose values
        6. Read the AK system purpose values and assert system purpose values have changed

    :CaseImportance: Medium

    :BZ: 1789028
    """
    # Requires Cls org and manifest. Manifest is for self-support values.
    # Create an AK with no system purpose values set
    org = module_sca_manifest_org
    new_ak = module_target_sat.cli_factory.make_activation_key({'organization-id': org.id})
    # Assert system purpose values are null after creating the AK and adding the manifest.
    assert new_ak['system-purpose']['purpose-addons'] == ''
    assert new_ak['system-purpose']['purpose-role'] == ''
    assert new_ak['system-purpose']['purpose-usage'] == ''

    # Check that system purpose values can be added to an AK.
    module_target_sat.cli.ActivationKey.update(
        {
            'id': new_ak['id'],
            'purpose-addons': "test-addon1, test-addon2",
            'purpose-role': "test-role1",
            'purpose-usage': "test-usage1",
            'service-level': "Self-Support",
            'organization-id': org.id,
        }
    )
    updated_ak = module_target_sat.cli.ActivationKey.info(
        {'id': new_ak['id'], 'organization-id': org.id}
    )
    assert updated_ak['system-purpose']['purpose-addons'] == "test-addon1, test-addon2"
    assert updated_ak['system-purpose']['purpose-role'] == "test-role1"
    assert updated_ak['system-purpose']['purpose-usage'] == "test-usage1"
    assert updated_ak['system-purpose']['service-level'] == "Self-Support"
    # Check that system purpose values can be updated
    module_target_sat.cli.ActivationKey.update(
        {
            'id': new_ak['id'],
            'purpose-addons': "test-addon3, test-addon4",
            'purpose-role': "test-role2",
            'purpose-usage': "test-usage2",
            'service-level': "Premium",
            'organization-id': org.id,
        }
    )
    updated_ak = module_target_sat.cli.ActivationKey.info(
        {'id': new_ak['id'], 'organization-id': org.id}
    )
    assert updated_ak['system-purpose']['purpose-addons'] == "test-addon3, test-addon4"
    assert updated_ak['system-purpose']['purpose-role'] == "test-role2"
    assert updated_ak['system-purpose']['purpose-usage'] == "test-usage2"
    assert updated_ak['system-purpose']['service-level'] == "Premium"


@pytest.mark.tier1
@pytest.mark.parametrize('new_name', **parametrized(valid_data_list()))
def test_positive_copy_by_parent_id(module_org, new_name, module_target_sat):
    """Copy Activation key for all valid Activation Key name
    variations

    :id: c9ad8aff-07ba-4804-a198-f719fe905123

    :expectedresults: Activation key is successfully copied

    :CaseImportance: Critical

    :parametrized: yes
    """
    parent_ak = module_target_sat.cli_factory.make_activation_key(
        {'organization-id': module_org.id}
    )
    result = module_target_sat.cli.ActivationKey.copy(
        {'id': parent_ak['id'], 'new-name': new_name, 'organization-id': module_org.id}
    )
    assert 'Activation key copied.' in result


@pytest.mark.tier1
def test_positive_copy_by_parent_name(module_org, module_target_sat):
    """Copy Activation key by passing name of parent

    :id: 5d5405e6-3b26-47a3-96ff-f6c0f6c32607

    :expectedresults: Activation key is successfully copied

    :CaseImportance: Critical
    """
    parent_ak = module_target_sat.cli_factory.make_activation_key(
        {'organization-id': module_org.id}
    )
    result = module_target_sat.cli.ActivationKey.copy(
        {
            'name': parent_ak['name'],
            'new-name': gen_string('alpha'),
            'organization-id': module_org.id,
        }
    )
    assert 'Activation key copied.' in result


@pytest.mark.tier1
def test_negative_copy_with_same_name(module_org, module_target_sat):
    """Copy activation key with duplicate name

    :id: f867c468-4155-495c-a1e5-c04d9868a2e0

    :expectedresults: Activation key is not successfully copied
    """
    parent_ak = module_target_sat.cli_factory.make_activation_key(
        {'organization-id': module_org.id}
    )
    with pytest.raises(CLIReturnCodeError) as raise_ctx:
        module_target_sat.cli.ActivationKey.copy(
            {
                'name': parent_ak['name'],
                'new-name': parent_ak['name'],
                'organization-id': module_org.id,
            }
        )
    assert raise_ctx.value.status == 65
    assert "Validation failed: Name has already been taken" in raise_ctx.value.message


@pytest.mark.run_in_one_thread
@pytest.mark.skip_if_not_set('fake_manifest')
@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_copy_activationkey_and_check_content(
    function_sca_manifest_org, module_target_sat
):
    """Copy Activation key and verify contents

    :id: f4ee8096-4120-4d06-8c9a-57ac1eaa8f68

    :steps:

        1. Create parent key and add content
        2. Copy Activation key by passing id of parent
        3. Verify content was successfully copied

    :expectedresults: Activation key is successfully copied
    """
    # Begin test setup
    org = function_sca_manifest_org
    result = module_target_sat.cli_factory.setup_org_for_a_rh_repo(
        {
            'product': PRDS['rhel'],
            'repository-set': REPOSET['rhst7'],
            'repository': REPOS['rhst7']['name'],
            'organization-id': org.id,
        },
        force_use_cdn=True,
    )
    content = module_target_sat.cli.ActivationKey.product_content(
        {'id': result['activationkey-id'], 'organization-id': org.id}
    )
    assert content[0]['name'] == REPOSET['rhst7']
    # End test setup
    new_name = gen_string('utf8')
    copy_ak = module_target_sat.cli.ActivationKey.copy(
        {'id': result['activationkey-id'], 'new-name': new_name, 'organization-id': org.id}
    )
    assert 'Activation key copied.' in copy_ak
    new_content = module_target_sat.cli.ActivationKey.product_content(
        {'id': result['activationkey-id'], 'organization-id': org.id}
    )
    assert new_content[0]['name'] == REPOSET['rhst7']


@pytest.mark.tier1
def test_positive_update_autoattach_toggle(module_org, module_target_sat):
    """Update Activation key with inverse auto-attach value

    :id: de3b5fb7-7963-420a-b4c9-c66e78a111dc

    :steps:

        1. Get the key's current auto attach value.
        2. Update the key with the value's inverse.
        3. Verify key was updated.

    :expectedresults: Activation key is successfully copied

    :CaseImportance: Critical
    """
    new_ak = module_target_sat.cli_factory.make_activation_key({'organization-id': module_org.id})
    attach_value = new_ak['auto-attach']
    # invert value
    new_value = 'false' if attach_value == 'true' else 'true'
    module_target_sat.cli.ActivationKey.update(
        {'auto-attach': new_value, 'id': new_ak['id'], 'organization-id': module_org.id}
    )
    updated_ak = module_target_sat.cli.ActivationKey.info({'id': new_ak['id']})
    assert updated_ak['auto-attach'] == new_value


@pytest.mark.tier1
def test_positive_update_autoattach(module_org, module_target_sat):
    """Update Activation key with valid auto-attach values

    :id: 9e18b950-6f0f-4f82-a3ac-ef6aba950a78

    :expectedresults: Activation key is successfully updated

    :CaseImportance: Critical
    """
    new_ak = module_target_sat.cli_factory.make_activation_key({'organization-id': module_org.id})
    for new_value in ('1', '0', 'true', 'false', 'yes', 'no'):
        result = module_target_sat.cli.ActivationKey.update(
            {'auto-attach': new_value, 'id': new_ak['id'], 'organization-id': module_org.id}
        )
        assert result[0]['message'] == 'Activation key updated.'


@pytest.mark.tier2
def test_negative_update_autoattach(module_org, module_target_sat):
    """Attempt to update Activation key with bad auto-attach value

    :id: 54b6f808-ff54-4e69-a54d-e1f99a4652f9

    :steps:

        1. Attempt to update a key with incorrect auto-attach value
        2. Verify that an appropriate error message was returned

    :expectedresults: Activation key is not updated. Appropriate error
        shown.

    :CaseImportance: Low
    """
    new_ak = module_target_sat.cli_factory.make_activation_key({'organization-id': module_org.id})
    with pytest.raises(CLIReturnCodeError) as exe:
        module_target_sat.cli.ActivationKey.update(
            {
                'auto-attach': gen_string('utf8'),
                'id': new_ak['id'],
                'organization-id': module_org.id,
            }
        )
    assert "'--auto-attach': value must be one of" in exe.value.stderr.lower()


@pytest.mark.tier3
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_content_override(module_org, module_target_sat):
    """Positive content override

    :id: a4912cc0-3bf7-4e90-bb51-ec88b2fad227

    :steps:

        1. Create activation key and add content
        2. Get the first product's label
        3. Override the product's content enabled state
        4. Verify that the command succeeded

    :expectedresults: Activation key content override was successful
    """
    result = module_target_sat.cli_factory.setup_org_for_a_custom_repo(
        {'url': settings.repos.yum_0.url, 'organization-id': module_org.id}
    )
    content = module_target_sat.cli.ActivationKey.product_content(
        {'id': result['activationkey-id'], 'organization-id': module_org.id}
    )
    for override_value in (True, False):
        module_target_sat.cli.ActivationKey.content_override(
            {
                'content-label': content[0]['label'],
                'id': result['activationkey-id'],
                'organization-id': module_org.id,
                'value': int(override_value),
            }
        )
        # Retrieve the product content enabled flag
        content = module_target_sat.cli.ActivationKey.product_content(
            {'id': result['activationkey-id'], 'organization-id': module_org.id}
        )
        assert content[0]['override'] == f'enabled:{int(override_value)}'


@pytest.mark.tier2
def test_positive_remove_user(module_org, module_target_sat):
    """Delete any user who has previously created an activation key
    and check that activation key still exists

    :id: ba9c4b29-2349-47ea-8081-917de2c17ed2

    :expectedresults: Activation Key can be read

    :BZ: 1291271
    """
    password = gen_string('alpha')
    user = module_target_sat.cli_factory.user({'password': password, 'admin': 'true'})
    ak = module_target_sat.cli.ActivationKey.with_user(
        username=user['login'], password=password
    ).create({'name': gen_string('alpha'), 'organization-id': module_org.id})
    module_target_sat.cli.User.delete({'id': user['id']})
    try:
        module_target_sat.cli.ActivationKey.info({'id': ak['id']})
    except CLIReturnCodeError:
        pytest.fail("Activation key can't be read")


@pytest.mark.run_in_one_thread
@pytest.mark.tier3
def test_positive_view_content_by_non_admin_user(function_sca_manifest_org, module_target_sat):
    """Attempt to read activation key content by non admin user

    :id: af75b640-97be-431b-8ac0-a6367f8f1996

    :customerscenario: true

    :steps:

        1. As admin user create an activation
        2. As admin user enable a repository on an activation key
        3. Setup a non admin User with the following permissions
            Katello::ActivationKey:
                view_activation_keys, create_activation_keys,
                edit_activation_keys, destroy_activation_keys
                Search: "name ~ ak_test"
            Katello::HostCollection:
                view_host_collections, edit_host_collections
                Search: "name ~ "Test_*_Dev" || name ~ "Test_*_QA"
            Organization:
                view_organizations, assign_organizations,
            Katello::Product:
                view_products, edit_products, sync_products,
                create_products, destroy_products


    :expectedresults: The non admin user can view the activation key
        repository sets

    :BZ: 1406076
    """
    org = function_sca_manifest_org
    user_name = gen_alphanumeric()
    user_password = gen_alphanumeric()
    hc_names_like = (
        f'Test_*_{gen_string("alpha")}',
        f'Test_*_{gen_string("alpha")}',
    )
    result = module_target_sat.cli_factory.setup_org_for_a_rh_repo(
        {
            'product': REPOS['rhst7']['product'],
            'repository-set': REPOS['rhst7']['reposet'],
            'repository': REPOS['rhst7']['name'],
            'organization-id': org.id,
        },
        force_use_cdn=True,
    )
    content = module_target_sat.cli.ActivationKey.product_content(
        {'id': result['activationkey-id'], 'organization-id': org.id}
    )
    assert content[0]['name'] == REPOSET['rhst7']
    ak_name = module_target_sat.cli.ActivationKey.info({'id': result['activationkey-id']})['name']
    role = module_target_sat.cli_factory.make_role({'organization-id': org.id})
    resource_permissions = {
        'Katello::ActivationKey': {
            'permissions': [
                'view_activation_keys',
                'create_activation_keys',
                'edit_activation_keys',
                'destroy_activation_keys',
            ],
            'search': f"name ~ {ak_name}",
        },
        'Katello::HostCollection': {
            'permissions': ['view_host_collections', 'edit_host_collections'],
            'search': f'name ~ {hc_names_like[0]} || name ~ {hc_names_like[1]}',
        },
        'Organization': {'permissions': ['view_organizations', 'assign_organizations']},
        'Katello::Product': {
            'permissions': [
                'view_products',
                'edit_products',
                'sync_products',
                'create_products',
                'destroy_products',
            ]
        },
    }
    module_target_sat.cli_factory.add_role_permissions(role['id'], resource_permissions)
    user = module_target_sat.cli_factory.user(
        {
            'admin': False,
            'default-organization-id': org.id,
            'organization-ids': [org.id],
            'login': user_name,
            'password': user_password,
        }
    )
    module_target_sat.cli.User.add_role({'id': user['id'], 'role-id': role['id']})
    ak_user_cli_session = module_target_sat.cli.ActivationKey.with_user(user_name, user_password)
    reposet = ak_user_cli_session.product_content(
        {'id': result['activationkey-id'], 'organization-id': org.id}
    )
    assert len(reposet) == 1
    assert reposet[0]['id'] == content[0]['id']


@pytest.mark.tier3
def test_positive_ak_with_custom_product_on_rhel6(
    module_org, module_location, rhel6_contenthost, target_sat
):
    """Registering a rhel6 host using an ak with custom repos should not fail

    :id: d02c2664-8034-4562-914a-3b68f0c35b32

    :customerscenario: true

    :steps:
        1. Create a custom repo
        2. Create ak and add custom repo to ak
        3. Register a rhel6 chost with the ak

    :expectedresults: Host is registered successfully

    :bz: 2038388
    """
    entities_ids = target_sat.cli_factory.setup_org_for_a_custom_repo(
        {'url': settings.repos.yum_1.url, 'organization-id': module_org.id}
    )
    ak = target_sat.api.ActivationKey(id=entities_ids['activationkey-id']).read()
    result = rhel6_contenthost.register(module_org.label, module_location, ak.name, target_sat)
    assert 'The system has been registered with ID' in result.stdout


@pytest.mark.tier3
def test_positive_invalid_release_version(module_sca_manifest_org, module_target_sat):
    """Check invalid release versions when updating or creating an activation key

    :id: 2efe452f-132c-4831-abfb-62305832ac66

    :customerscenario: true

    :Steps:
        1. Attempt to create an activation key with a invalid release version
        2. Attempt to update an activation key with a invalid release version
        3. Successfully update an activation key with a valid release version

    :expectedresults: Invalid release versions should fail and valid release version should succeed

    :BZ: 1895976
    """

    name = gen_string('alpha')
    activation_key = module_target_sat.cli_factory.make_activation_key(
        {'organization-id': module_sca_manifest_org.id, 'name': name}
    )
    rh_repo_id = module_target_sat.api_factory.enable_rhrepo_and_fetchid(
        basearch=DEFAULT_ARCHITECTURE,
        org_id=module_sca_manifest_org.id,
        product=REPOS['kickstart']['rhel8_aps']['product'],
        repo=REPOS['kickstart']['rhel8_aps']['name'],
        reposet=REPOS['kickstart']['rhel8_aps']['reposet'],
        releasever=REPOS['kickstart']['rhel8_aps']['version'],
    )
    module_target_sat.cli.Repository.synchronize({'id': rh_repo_id})
    with pytest.raises(CLIFactoryError) as error:
        module_target_sat.cli_factory.make_activation_key(
            {
                'organization-id': module_sca_manifest_org.id,
                'name': name,
                'release-version': 'ThisShouldNotWork',
            }
        )
    assert 'Invalid release version: [ThisShouldNotWork]' in error.value.args[0]

    with pytest.raises(CLIReturnCodeError) as error:
        module_target_sat.cli.ActivationKey.update(
            {
                'name': activation_key['name'],
                'organization-id': module_sca_manifest_org.id,
                'release-version': 'ThisShouldAlsoNotWork',
            }
        )
    assert 'Invalid release version: [ThisShouldAlsoNotWork]' in error.value.args[0]
    update_ak = module_target_sat.cli.ActivationKey.update(
        {
            'name': activation_key['name'],
            'organization-id': module_sca_manifest_org.id,
            'release-version': REPOS['kickstart']['rhel8_aps']['version'],
        }
    )
    assert update_ak[0]['message'] == 'Activation key updated.'
