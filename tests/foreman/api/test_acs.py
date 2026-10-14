"""Tests for Alternate Content Sources API

:Requirement: AlternateContentSources

:CaseAutomation: Automated

:CaseComponent: AlternateContentSources

:Team: Artemis

:CaseImportance: High

"""

from fauxfactory import gen_string
import pytest
from requests.exceptions import HTTPError

from robottelo.config import settings
from robottelo.constants.repos import PULP_FIXTURE_ROOT, PULP_SUBPATHS_COMBINED


@pytest.mark.e2e
@pytest.mark.upgrade
@pytest.mark.parametrize(
    ('acs_type', 'cnt_type'),
    [
        (acs, cnt)
        for acs in ['custom', 'simplified', 'rhui']
        for cnt in ['yum', 'file']
        if not (acs == 'rhui' and cnt == 'file')  # invalid combination: 'rhui-file'
    ],
)
@pytest.mark.network_sensitive
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

    # Create
    params = {
        'name': gen_string('alpha'),
        'alternate_content_source_type': acs_type,
        'content_type': cnt_type,
        'smart_proxy_ids': [module_target_sat.nailgun_capsule.id],
    }

    # In case of IPv6, set 'ACS HTTP proxy' of the bound capsule to the IPv6 proxy
    # This is necessary for the Refresh to succeed.
    if not settings.server.network_type.has_ipv4:
        caps = module_target_sat.nailgun_smart_proxy
        caps.http_proxy = module_target_sat.enable_satellite_http_proxy()
        caps.update(['http_proxy'])
        params.update({'use_http_proxies': True})

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


@pytest.mark.foremanctl
@pytest.mark.parametrize('proxy_field', ['smart_proxy_ids', 'smart_proxy_names'])
def test_negative_reject_non_pulp_proxy_for_acs_create_update(
    request, module_target_sat, proxy_field
):
    """Only the content smart proxy can be assigned to an ACS.

    :id: 8a75a904-12bf-4288-99e8-78044059e830

    :parametrized: yes

    :steps:
        1. Identify the Satellite's content and management smart proxies.
        2. Create an ACS with the content proxy.
        3. Try to update the ACS with the management proxy.
        4. Remove its proxy and assign the content proxy again.
        5. Try to create an ACS with the management proxy.

    :expectedresults:
        1. The content proxy can be assigned during creation and update.
        2. The management proxy update is rejected without changing the ACS's proxies.
        3. Creation with the management proxy is rejected without creating an ACS.
    """
    # 1. Identify the Satellite's content and management smart proxies.
    content_proxy = module_target_sat.nailgun_content_smart_proxy
    management_proxy = module_target_sat.nailgun_smart_proxy
    assert content_proxy.id != management_proxy.id

    proxy_attribute = 'id' if proxy_field == 'smart_proxy_ids' else 'name'
    content_value = getattr(content_proxy, proxy_attribute)
    management_value = getattr(management_proxy, proxy_attribute)
    error_msg = 'must have the Pulp feature to be used with alternate content sources'

    # 2. Create an ACS with the content proxy.
    acs_params = {
        'name': gen_string('alpha'),
        'alternate_content_source_type': 'custom',
        'content_type': 'yum',
        'base_url': PULP_FIXTURE_ROOT,
        'subpaths': PULP_SUBPATHS_COMBINED['yum'],
        'verify_ssl': False,
    }
    acs = module_target_sat.api.AlternateContentSource(
        **acs_params, **{proxy_field: [content_value]}
    ).create()
    request.addfinalizer(acs.delete)
    assert [proxy.id for proxy in acs.read().smart_proxies] == [content_proxy.id]

    # 3. Try to update the ACS with the management proxy.
    setattr(acs, proxy_field, [management_value])
    with pytest.raises(HTTPError) as update_error:
        acs.update([proxy_field])
    assert update_error.value.response.status_code == 422
    assert error_msg in update_error.value.response.text
    assert management_proxy.name in update_error.value.response.text
    assert [proxy.id for proxy in acs.read().smart_proxies] == [content_proxy.id]

    # 4. Remove its proxy and assign the content proxy again.
    setattr(acs, proxy_field, [])
    acs.update([proxy_field])
    assert not acs.read().smart_proxies
    setattr(acs, proxy_field, [content_value])
    acs.update([proxy_field])
    assert [proxy.id for proxy in acs.read().smart_proxies] == [content_proxy.id]

    # 5. Try to create an ACS with the management proxy.
    non_pulp_params = {
        **acs_params,
        'name': gen_string('alpha'),
        proxy_field: [management_value],
    }
    with pytest.raises(HTTPError) as create_error:
        module_target_sat.api.AlternateContentSource(**non_pulp_params).create()
    assert create_error.value.response.status_code == 422
    assert error_msg in create_error.value.response.text
    assert management_proxy.name in create_error.value.response.text
    assert not module_target_sat.api.AlternateContentSource().search(
        query={'search': f'name="{non_pulp_params["name"]}"'}
    )


def test_positive_run_bulk_actions(module_target_sat, module_yum_repo):
    """Perform bulk actions with an ACS.

    :id: 00ff25c1-fe87-43d7-950f-8cc579d75d6b

    :steps:
        1. Create several ACSes.
        2. Bulk refresh them all.
        3. Add 1 more ACS, then use bulk refresh all.
        4. Bulk destroy some of them.
        5. Cleanup the rest.

    :expectedresults:
        1. All ACSes can be refreshed via bulk action.
        2. Only the proper ACSes are deleted on bulk destroy.
    """
    params = {
        'alternate_content_source_type': 'simplified',
        'content_type': 'yum',
        'smart_proxy_ids': [module_target_sat.nailgun_capsule.id],
        'product_ids': [module_yum_repo.product.id],
    }

    # In case of IPv6, set 'ACS HTTP proxy' of the bound capsule to the IPv6 proxy
    # This is necessary for the Refresh to succeed.
    if not settings.server.network_type.has_ipv4:
        caps = module_target_sat.nailgun_smart_proxy
        caps.http_proxy = module_target_sat.enable_satellite_http_proxy()
        caps.update(['http_proxy'])
        params.update({'use_http_proxies': True})

    acs_ids = []
    for _ in range(3):
        params['name'] = gen_string('alpha')
        acs = module_target_sat.api.AlternateContentSource(**params).create()
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
    # Add another ACS and then bulk refresh all
    params['name'] = gen_string('alpha')
    acs = module_target_sat.api.AlternateContentSource(**params).create()
    acs_ids.append(acs.id)
    res = module_target_sat.api.AlternateContentSource().bulk_refresh_all()
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
