"""Test class for Alternate Content Sources CLI

:Requirement: AlternateContentSources

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: AlternateContentSources

:Team: Phoenix-content

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_alphanumeric

from robottelo.cli.base import CLIReturnCodeError
from robottelo.constants.repos import PULP_FIXTURE_ROOT
from robottelo.constants.repos import PULP_SUBPATHS_COMBINED

ACS_UPDATED = 'Alternate Content Source updated.'
ACS_DELETED = 'Alternate Content Source deleted.'
ACS_NOT_FOUND = 'Could not find alternate_content_source resource with id'

VAL_FAILED = 'Validation failed'
VAL_CANT_BLANK = 'can\'t be blank'
VAL_MUST_BLANK = 'must be blank'
VAL_CANNOT_BE = 'cannot be'


@pytest.mark.e2e
@pytest.mark.tier2
@pytest.mark.parametrize('cnt_type', ['yum', 'file'])
@pytest.mark.parametrize('acs_type', ['custom', 'simplified', 'rhui'])
def test_positive_CRUD_all_types(
    request, module_target_sat, acs_type, cnt_type, module_yum_repo, module_file_repo
):
    """Create, read, update, refresh and delete ACSes of all supported types.

    :id: 3d51b810-f81f-4d09-80a1-4f27fda4e84f

    :parametrized: yes

    :steps:
        1. Create an ACS using necessary params.
        2. List it, read it.
        3. Update name and description.
        4. Refresh it.
        5. Delete it.

    :expectedresults:
        1. ACS can be created.
        2. ACS can be listed and read with correct values.
        3. ACS can be updated and read with new name.
        4. ACS can be refreshed.
        5. ACS can be deleted.

    """
    if 'rhui' in request.node.name and 'file' in request.node.name:
        pytest.skip('unsupported parametrize combination')

    # Create
    params = {
        'name': gen_alphanumeric(),
        'alternate-content-source-type': acs_type,
        'content-type': cnt_type,
        'smart-proxy-ids': module_target_sat.nailgun_capsule.id,
    }

    if acs_type == 'simplified':
        params.update(
            {'product-ids': [module_yum_repo.product.id]}
            if cnt_type == 'yum'
            else {'product-ids': [module_file_repo.product.id]}
        )
    else:
        params.update(
            {
                'base-url': PULP_FIXTURE_ROOT,
                'subpaths': PULP_SUBPATHS_COMBINED[cnt_type],
                'verify-ssl': 'false',
            }
        )

    new_acs = module_target_sat.cli.ACS.create(params)

    # List
    list = module_target_sat.cli.ACS.list({'search': f'name={new_acs["name"]}'})
    assert len(list) == 1
    assert list[0]['id'] == new_acs['id'], 'the listed id of ACS does not match the created one'
    assert (
        list[0]['type'] == new_acs['alternate-content-source-type']
    ), 'the listed type of ACS does not match the created one'

    # Read
    acs_info = module_target_sat.cli.ACS.info({'id': new_acs['id']})
    assert acs_info == new_acs, 'ACS values do not fit the ones from creation time.'

    # Update
    new_name = gen_alphanumeric()
    new_desc = gen_alphanumeric()
    result = module_target_sat.cli.ACS.update(
        {'id': new_acs['id'], 'name': new_name, 'description': new_desc}
    )
    assert ACS_UPDATED in str(result), 'update notification is missing or wrong'
    acs_info = module_target_sat.cli.ACS.info({'name': new_name})
    assert acs_info['name'] == new_name, 'ACS name was not updated properly'
    assert acs_info['description'] == new_desc, 'ACS description was not updated properly'

    # Refresh by id, name
    module_target_sat.cli.ACS.refresh({'id': new_acs['id']})
    module_target_sat.cli.ACS.refresh({'name': new_name})

    # Delete
    result = module_target_sat.cli.ACS.delete({'id': new_acs['id']})
    assert ACS_DELETED in str(result), 'delete notification is missing or wrong'
    with pytest.raises(CLIReturnCodeError) as context:
        module_target_sat.cli.ACS.info({'id': new_acs['id']})
    assert f'{ACS_NOT_FOUND} {new_acs["id"]}.' in context.value.message, 'ACS was not deleted'


@pytest.mark.tier2
@pytest.mark.parametrize('acs_type', ['custom', 'simplified', 'rhui'])
def test_negative_check_name_validation(module_target_sat, acs_type):
    """Check validation when name is not provided.

    :id: 3cb1474f-b8bb-47ab-8884-3fed69041e90

    :parametrized: yes

    :CaseImportance: Medium

    :BZ: 2159967

    :steps:
        1. Try to create an ACS without name provided.

    :expectedresults:
        1. Should fail with validation error and proper message.

    """
    with pytest.raises(CLIReturnCodeError) as context:
        module_target_sat.cli.ACS.create({'alternate-content-source-type': acs_type})
    assert VAL_FAILED in context.value.message, 'validation notification is missing or wrong'
    assert f'Name {VAL_CANT_BLANK}' in context.value.message


@pytest.mark.tier2
@pytest.mark.parametrize('acs_type', ['custom', 'rhui'])
def test_negative_check_custom_rhui_validations(module_target_sat, acs_type, module_yum_repo):
    """Check validations for required and forbidden params specific to Custom and Rhui ACS.

    :id: 5361e66f-b7b9-411d-bb9e-43275d6676be

    :parametrized: yes

    :CaseImportance: Medium

    :steps:
        1. Try to create an ACS without base-url and verify-ssl provided.
        2. Try to create an ACS with product-ids provided.

    :expectedresults:
        1. Should fail as base-url and verify-ssl are required.
        2. Should fail as product-ids is forbidden.

    """
    # Create with required missing
    with pytest.raises(CLIReturnCodeError) as context:
        module_target_sat.cli.ACS.create(
            {'name': gen_alphanumeric(), 'alternate-content-source-type': acs_type}
        )
    assert VAL_FAILED in context.value.message, 'validation notification is missing or wrong'
    assert f'Base url {VAL_CANT_BLANK}' in context.value.message
    assert (
        f'Verify ssl {VAL_CANT_BLANK}' in context.value.message
        or 'Verify ssl must be provided' in context.value.message
    )

    # Create with forbidden present
    with pytest.raises(CLIReturnCodeError) as context:
        module_target_sat.cli.ACS.create(
            {
                'name': gen_alphanumeric(),
                'alternate-content-source-type': acs_type,
                'base-url': PULP_FIXTURE_ROOT,
                'verify-ssl': 'false',
                'product-ids': module_yum_repo.product.id,
            }
        )
    assert VAL_FAILED in context.value.message, 'validation notification is missing or wrong'
    assert (
        f'Products {VAL_MUST_BLANK}' in context.value.message
        or f'Product ids {VAL_CANNOT_BE} set' in context.value.message
    )


@pytest.mark.tier2
@pytest.mark.parametrize('cnt_type', ['yum', 'file'])
def test_negative_check_simplified_validations(
    module_target_sat, cnt_type, module_yum_repo, module_file_repo
):
    """Check validations for forbidden params specific to Simplified ACS.

    :id: 4b975e9f-4950-4834-a3ed-0c0aa873ce51

    :parametrized: yes

    :CaseImportance: Medium

    :steps:
        1. Try to create Simplified ACS with multiple forbidden parameters provided.

    :expectedresults:
        1. Should fail and list all the forbidden parameters must be blank.

    """
    # Create with forbidden present
    params = {
        'name': gen_alphanumeric(),
        'alternate-content-source-type': 'simplified',
        'content-type': cnt_type,
        'smart-proxy-ids': module_target_sat.nailgun_capsule.id,
        # forbidden options
        'base-url': PULP_FIXTURE_ROOT,
        'subpaths': f'{gen_alphanumeric()}/',
        'verify-ssl': 'false',
        'ssl-ca-cert-id': '1',
        'ssl-client-cert-id': '1',
        'ssl-client-key-id': '1',
        'upstream-username': gen_alphanumeric(),
        'upstream-password': gen_alphanumeric(),
    }
    params.update(
        {'product-ids': [module_yum_repo.product.id]}
        if cnt_type == 'yum'
        else {'product-ids': [module_file_repo.product.id]}
    )
    with pytest.raises(CLIReturnCodeError) as context:
        module_target_sat.cli.ACS.create(params)
    assert VAL_FAILED in context.value.message, 'validation notification is missing or wrong'
    assert f'Base url {VAL_MUST_BLANK}' in context.value.message
    assert f'Subpaths {VAL_MUST_BLANK}' in context.value.message
    assert (
        f'Verify ssl {VAL_MUST_BLANK}' in context.value.message
        or f'Verify ssl {VAL_CANNOT_BE} provided' in context.value.message
    )
    assert (
        f'Ssl ca cert {VAL_MUST_BLANK}' in context.value.message
        or f'Ssl ca cert {VAL_CANNOT_BE} set' in context.value.message
    )
    assert (
        f'Ssl client cert {VAL_MUST_BLANK}' in context.value.message
        or f'Ssl client cert {VAL_CANNOT_BE} set' in context.value.message
    )
    assert (
        f'Ssl client key {VAL_MUST_BLANK}' in context.value.message
        or f'Ssl client key {VAL_CANNOT_BE} set' in context.value.message
    )
    assert f'Upstream username {VAL_MUST_BLANK}' in context.value.message
    assert f'Upstream password {VAL_MUST_BLANK}' in context.value.message
