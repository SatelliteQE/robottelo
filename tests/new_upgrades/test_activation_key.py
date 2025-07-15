"""Test Activation Key related Upgrade Scenario's

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseComponent: ActivationKeys

:Team: Phoenix-subscriptions

:CaseImportance: High

"""

from box import Box
from fauxfactory import gen_alpha
import pytest
from requests.exceptions import HTTPError

from robottelo.config import settings
from robottelo.utils.shared_resource import SharedResource


@pytest.fixture
def ak_upgrade_setup(content_upgrade_shared_satellite, upgrade_action):
    """Pre-upgrade scenario that creates an activation key and custom repo.

    :id: preupgrade-a7443b54-eb2e-497b-8a50-92abeae01496

    :steps:
        1. Create organization.
        2. Create product.
        3. Create and sync custom repo.
        4. Create activation key.
    """
    target_sat = content_upgrade_shared_satellite
    with SharedResource(target_sat.hostname, upgrade_action, target_sat=target_sat) as sat_upgrade:
        test_data = Box(
            {
                'target_sat': target_sat,
                'test_name': None,
                'org': None,
                'product': None,
                'repo': None,
                'cv': None,
                'ak': None,
            }
        )
        test_name = f'ak_upgrade_{gen_alpha()}'
        test_data.test_name = test_name
        org = target_sat.api.Organization(name=f"{test_name}_org").create()
        test_data.org = org
        product = target_sat.api.Product(organization=org, name=f'{test_name}_prod').create()
        test_data.product = product
        custom_repo = target_sat.api.Repository(
            product=product,
            name=f'{test_name}_repo',
            url=settings.repos.yum_1.url,
            content_type='yum',
        ).create()
        test_data.repo = custom_repo
        custom_repo.sync()
        cv = target_sat.publish_content_view(org, [custom_repo], f'{test_name}_cv')
        assert len(cv.read_json()['versions']) == 1
        test_data.cv = cv
        ak = target_sat.api.ActivationKey(
            content_view=cv, organization=org, environment=org.library.id, name=f'{test_name}_ak'
        ).create()
        test_data.ak = ak
        ak.host_collection.append(
            target_sat.api.HostCollection(organization=org, name=f'{test_name}_hc').create()
        )
        ak = ak.update(['host_collection'])
        assert len(ak.host_collection) == 1
        sat_upgrade.ready()
        target_sat._session = None
        yield test_data


@pytest.mark.content_upgrades
def test_ak_upgrade_scenario(ak_upgrade_setup):
    """After Upgrade, Activation keys entities remain the same and
    all their functionality works.

    :id: postupgrade-a7443b54-eb2e-497b-8a50-92abeae01496

    :steps:
        1. Postupgrade, Verify activation key has same entities associated.
        2. Update existing activation key with new entities.
        3. Delete activation key.

    :expectedresults: Activation key's entities should be same after upgrade and activation
        key update and delete should work.

    :BlockedBy: SAT-28048, SAT-28990
    """
    target_sat = ak_upgrade_setup.target_sat
    target_sat._swap_nailgun(f"{settings.UPGRADE.TO_VERSION}.z")
    org = target_sat.api.Organization().search(
        query={'search': f'name={ak_upgrade_setup.org.name}'}
    )[0]
    ak = target_sat.api.ActivationKey(organization=org.id).search(
        query={'search': f'name={ak_upgrade_setup.ak.name}'}
    )[0]
    cv = target_sat.api.ContentView(organization=org.id).search(
        query={'search': f'name={ak_upgrade_setup.cv.name}'}
    )[0]
    assert f'{ak_upgrade_setup.test_name}_ak' == ak.name
    assert f'{ak_upgrade_setup.test_name}_cv' == cv.name
    assert ak.content_view.id == cv.id
    ak.host_collection.append(
        target_sat.api.HostCollection(
            organization=org, name=f'{ak_upgrade_setup.test_name}_hc2'
        ).create()
    )
    ak.update(['host_collection'])
    assert len(ak.host_collection) == 2
    product2 = target_sat.api.Product(
        organization=org, name=f'{ak_upgrade_setup.test_name}_prod2'
    ).create()
    custom_repo2 = target_sat.api.Repository(
        product=product2,
        name=f'{ak_upgrade_setup.test_name}_repo2',
        url=settings.repos.yum_2.url,
        content_type='yum',
    ).create()
    custom_repo2.sync()
    cv2 = target_sat.api.ContentView(
        organization=org, repository=[custom_repo2.id], name=f'{ak_upgrade_setup.test_name}_cv2'
    ).create()
    cv2.publish()
    ak.delete()
    with pytest.raises(HTTPError):
        target_sat.api.ActivationKey(id=ak.id).read()
