"""Tests for Alternate Content Sources API

:Requirement: AlternateContentSources

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: AlternateContentSources

:Team: Phoenix-content

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_string
from requests.exceptions import HTTPError

from robottelo.constants.repos import PULP_FIXTURE_ROOT
from robottelo.constants.repos import PULP_SUBPATHS_COMBINED


@pytest.mark.e2e
@pytest.mark.tier2
@pytest.mark.upgrade
@pytest.mark.parametrize('cnt_type', ['yum', 'file'])
@pytest.mark.parametrize('acs_type', ['custom', 'simplified', 'rhui'])
def test_positive_CRUD_all_types(
    request, module_target_sat, acs_type, cnt_type, module_yum_repo, module_file_repo
):
    """Create, read, update, refresh and delete ACSes of all supported types.

    :id: 1c288663-cdb4-48e6-b03c-adaab96d6b67

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
        'name': gen_string('alpha'),
        'alternate_content_source_type': acs_type,
        'content_type': cnt_type,
        'smart_proxy_ids': [module_target_sat.nailgun_capsule.id],
    }

    if acs_type == 'simplified':
        params.update(
            {'product_ids': [module_yum_repo.product.id]}
            if cnt_type == 'yum'
            else {'product_ids': [module_file_repo.product.id]}
        )
    else:
        params.update(
            {
                'base_url': PULP_FIXTURE_ROOT,
                'subpaths': PULP_SUBPATHS_COMBINED[cnt_type],
                'verify_ssl': 'false',
            }
        )

    new_acs = module_target_sat.api.AlternateContentSource(**params).create()

    # List/search
    list = module_target_sat.api.AlternateContentSource().search(
        query={'search': f'name="{new_acs.name}"'}
    )
    assert len(list) == 1, 'zero or more than one ACSes listed'
    assert list[0].id == new_acs.id, 'the listed id of ACS does not match the created one'
    assert list[0].name == new_acs.name, 'the listed type of ACS does not match the created one'

    # Read
    read_acs = module_target_sat.api.AlternateContentSource(id=new_acs.id).read()
    common_props = {
        p for p in dir(read_acs) if not callable(getattr(read_acs, p)) and not p.startswith("_")
    } & {p for p in dir(new_acs) if not callable(getattr(new_acs, p)) and not p.startswith("_")}
    assert all([getattr(read_acs, p) == getattr(new_acs, p) for p in common_props])

    # Update
    new_acs.name = gen_string('alpha')
    new_acs.description = gen_string('alpha')
    new_acs.update(['name', 'description'])
    read_acs = module_target_sat.api.AlternateContentSource(id=new_acs.id).read()
    assert read_acs.name == new_acs.name, 'ACS name was not updated properly'
    assert read_acs.description == new_acs.description, 'ACS description was not updated properly'

    # Refresh
    assert new_acs.refresh()['result'] == 'success', 'ACS refresh did not succeed'

    # Delete
    module_target_sat.api.AlternateContentSource(id=new_acs.id).delete()
    with pytest.raises(HTTPError):
        module_target_sat.api.AlternateContentSource(id=new_acs.id).read()


@pytest.mark.tier2
def test_positive_run_bulk_actions(module_target_sat, module_yum_repo):
    """Perform bulk actions with an ACS.

    :id: 00ff25c1-fe87-43d7-950f-8cc579d75d6b

    :steps:
        1. Create several ACSes.
        2. Bulk refresh them all.
        3. Bulk destroy some of them.
        4. Cleanup the rest.

    :expectedresults:
        1. All ACSes can be refreshed via bulk action.
        2. Only the proper ACSes are deleted on bulk destroy.

    """
    acs_ids = []
    for i in range(3):
        acs = module_target_sat.api.AlternateContentSource(
            name=gen_string('alpha'),
            alternate_content_source_type='simplified',
            content_type='yum',
            smart_proxy_ids=[module_target_sat.nailgun_capsule.id],
            product_ids=[module_yum_repo.product.id],
        ).create()
        acs_ids.append(acs.id)

    res = module_target_sat.api.AlternateContentSource().bulk_refresh(data={'ids': acs_ids})
    assert res['result'] == 'success'
    assert all(
        [
            module_target_sat.api.AlternateContentSource(id=id).read().last_refresh['result']
            == 'success'
            for id in acs_ids
        ]
    )

    res = module_target_sat.api.AlternateContentSource().bulk_destroy(data={'ids': acs_ids[1:]})
    assert res['result'] == 'success'

    list = [item.id for item in module_target_sat.api.AlternateContentSource().search()]
    # assert the first stayed and rest was deleted
    assert acs_ids[0] in list
    assert acs_ids[1:] not in list

    module_target_sat.api.AlternateContentSource(id=acs_ids[0]).delete()
