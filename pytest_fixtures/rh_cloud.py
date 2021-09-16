import pytest
from nailgun import entities

from robottelo.config import settings
from robottelo.constants import DEFAULT_SUBSCRIPTION_NAME
from robottelo.constants import DISTRO_RHEL8


@pytest.fixture
def set_rh_cloud_token(default_sat):
    """A function-level fixture to set rh cloud token value."""
    default_sat.update_setting('rh_cloud_token', settings.rh_cloud.token)
    yield
    default_sat.update_setting('rh_cloud_token', '')


@pytest.fixture
def unset_rh_cloud_token(default_sat):
    """A function-level fixture to unset rh cloud token value."""
    yield
    default_sat.update_setting('rh_cloud_token', '')


@pytest.fixture(scope='module')
def organization_ak_setup(module_manifest_org):
    """A module-level fixture to create an Activation key in module_org"""
    ak = entities.ActivationKey(
        content_view=module_manifest_org.default_content_view,
        organization=module_manifest_org,
        environment=entities.LifecycleEnvironment(id=module_manifest_org.library.id),
        auto_attach=True,
    ).create()
    subscription = entities.Subscription(organization=module_manifest_org)
    subscription.refresh_manifest(data={'organization_id': module_manifest_org.id})
    default_subscription = subscription.search(
        query={'search': f'name="{DEFAULT_SUBSCRIPTION_NAME}"'}
    )[0]
    ak.add_subscriptions(data={'quantity': 10, 'subscription_id': default_subscription.id})
    yield module_manifest_org, ak
    ak.delete()


@pytest.fixture(scope='module')
def rhel8_insights_vm(default_sat, organization_ak_setup, rhel8_contenthost_module):
    """A module-level fixture to create rhel8 content host registered with insights."""
    org, ak = organization_ak_setup
    rhel8_contenthost_module.configure_rex(satellite=default_sat, org=org, register=False)
    rhel8_contenthost_module.configure_rhai_client(
        satellite=default_sat, activation_key=ak.name, org=org.label, rhel_distro=DISTRO_RHEL8
    )
    yield rhel8_contenthost_module


@pytest.fixture
def fixable_rhel8_vm(rhel8_insights_vm):
    """A function-level fixture to create dnf related insights recommendation for rhel8 host."""
    rhel8_insights_vm.run('dnf update -y dnf')
    rhel8_insights_vm.run('sed -i -e "/^best/d" /etc/dnf/dnf.conf')
    rhel8_insights_vm.run('insights-client')
