import pytest
from nailgun import entities

from robottelo.config import settings
from robottelo.constants import DEFAULT_SUBSCRIPTION_NAME
from robottelo.constants import DISTRO_RHEL8
from robottelo.helpers import add_remote_execution_ssh_key
from robottelo.rh_cloud_utils import setting_update


@pytest.fixture
def set_rh_cloud_token():
    """A function-level fixture to set rh cloud token value."""
    setting_update('rh_cloud_token', settings.rh_cloud.token)
    yield
    setting_update('rh_cloud_token', '')


@pytest.fixture
def unset_rh_cloud_token():
    """A function-level fixture to unset rh cloud token value."""
    yield
    setting_update('rh_cloud_token', '')


@pytest.fixture(scope='module')
def enable_lab_features():
    """A module-level fixture to enable lab features."""
    setting_update('lab_features', True)
    yield
    setting_update('lab_features', False)


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
    yield module_manifest_org, ak
    ak.delete()


@pytest.fixture(scope='module')
def rhel8_insights_vm(organization_ak_setup, rhel8_contenthost_module):
    """A module-level fixture to create rhel8 content host registered with insights."""
    org, ak = organization_ak_setup
    rhel8_contenthost_module.configure_rhai_client(
        activation_key=ak.name, org=org.label, rhel_distro=DISTRO_RHEL8
    )
    add_remote_execution_ssh_key(rhel8_contenthost_module.ip_addr)
    yield rhel8_contenthost_module


@pytest.fixture
def fixable_rhel8_vm(rhel8_insights_vm):
    """A function-level fixture to create dnf related insights recommendation for rhel8 host."""
    rhel8_insights_vm.run('dnf update -y dnf')
    rhel8_insights_vm.run('sed -i -e "/^best/d" /etc/dnf/dnf.conf')
    rhel8_insights_vm.run('insights-client')
