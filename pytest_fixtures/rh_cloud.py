import pytest
from nailgun import entities

from robottelo.constants import DEFAULT_SUBSCRIPTION_NAME


@pytest.fixture(scope='module')
def organization_ak_setup(module_manifest_org):
    """A module-level fixture to create an Activation key in module_org"""
    ak = entities.ActivationKey(
        content_view=module_manifest_org.default_content_view,
        organization=module_manifest_org,
        environment=entities.LifecycleEnvironment(id=module_manifest_org.library.id),
        auto_attach=True,
    ).create()
    subscription = entities.Subscription(organization=module_manifest_org).search(
        query={'search': f'name="{DEFAULT_SUBSCRIPTION_NAME}"'}
    )[0]
    ak.add_subscriptions(data={'quantity': 10, 'subscription_id': subscription.id})
    return module_manifest_org, ak
