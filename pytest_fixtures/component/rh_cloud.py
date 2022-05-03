import pytest
from broker.broker import VMBroker

from robottelo.config import settings
from robottelo.constants import DEFAULT_SUBSCRIPTION_NAME
from robottelo.constants import DISTRO_RHEL7
from robottelo.constants import DISTRO_RHEL8
from robottelo.helpers import file_downloader


@pytest.fixture(scope='module')
def rhcloud_sat_host(satellite_factory):
    """A module level fixture that provides a Satellite based on config settings"""
    new_sat = satellite_factory()
    yield new_sat
    VMBroker(hosts=[new_sat]).checkin()


@pytest.fixture(scope='module')
def rhcloud_manifest_org(rhcloud_sat_host):
    """A module level fixture to get organization with manifest."""
    org = rhcloud_sat_host.api.Organization().create()
    manifests_path = file_downloader(
        file_url=settings.fake_manifest.url['default'], hostname=rhcloud_sat_host.hostname
    )[0]
    rhcloud_sat_host.cli.Subscription.upload({'file': manifests_path, 'organization-id': org.id})
    return org


@pytest.fixture
def set_rh_cloud_token(rhcloud_sat_host):
    """A function-level fixture to set rh cloud token value."""
    rhcloud_sat_host.update_setting('rh_cloud_token', settings.rh_cloud.token)
    yield
    rhcloud_sat_host.update_setting('rh_cloud_token', '')


@pytest.fixture
def unset_rh_cloud_token(rhcloud_sat_host):
    """A function-level fixture to unset rh cloud token value."""
    yield
    rhcloud_sat_host.update_setting('rh_cloud_token', '')


@pytest.fixture(scope='module')
def organization_ak_setup(rhcloud_sat_host, rhcloud_manifest_org):
    """A module-level fixture to create an Activation key in module_org"""
    purpose_addons = "test-addon1, test-addon2"
    ak = rhcloud_sat_host.api.ActivationKey(
        content_view=rhcloud_manifest_org.default_content_view,
        organization=rhcloud_manifest_org,
        environment=rhcloud_sat_host.api.LifecycleEnvironment(id=rhcloud_manifest_org.library.id),
        purpose_addons=[purpose_addons],
        service_level='Self-Support',
        purpose_usage='test-usage',
        purpose_role='test-role',
        auto_attach=True,
    ).create()
    subscription = rhcloud_sat_host.api.Subscription(organization=rhcloud_manifest_org)
    # Disabling due to an issue with manifest refreshes. Is this refresh actually needed?
    # subscription.refresh_manifest(data={'organization_id': rhcloud_manifest_org.id})
    default_subscription = subscription.search(
        query={'search': f'name="{DEFAULT_SUBSCRIPTION_NAME}"'}
    )[0]
    ak.add_subscriptions(data={'quantity': 10, 'subscription_id': default_subscription.id})
    yield rhcloud_manifest_org, ak
    ak.delete()


@pytest.fixture(scope='module')
def rhcloud_registered_hosts(organization_ak_setup, content_hosts, rhcloud_sat_host):
    """Fixture that registers content hosts to Satellite and Insights."""
    org, ak = organization_ak_setup
    for vm in content_hosts:
        vm.configure_rhai_client(
            satellite=rhcloud_sat_host,
            activation_key=ak.name,
            org=org.label,
            rhel_distro=DISTRO_RHEL7,
        )
        assert vm.subscribed
    return content_hosts


@pytest.fixture(scope='module')
def rhel8_insights_vm(rhcloud_sat_host, organization_ak_setup, rhel8_contenthost_module):
    """A module-level fixture to create rhel8 content host registered with insights."""
    org, ak = organization_ak_setup
    rhel8_contenthost_module.configure_rex(satellite=rhcloud_sat_host, org=org, register=False)
    rhel8_contenthost_module.configure_rhai_client(
        satellite=rhcloud_sat_host, activation_key=ak.name, org=org.label, rhel_distro=DISTRO_RHEL8
    )
    yield rhel8_contenthost_module


@pytest.fixture
def fixable_rhel8_vm(rhel8_insights_vm):
    """A function-level fixture to create dnf related insights recommendation for rhel8 host."""
    rhel8_insights_vm.run('dnf update -y dnf')
    rhel8_insights_vm.run('sed -i -e "/^best/d" /etc/dnf/dnf.conf')
    rhel8_insights_vm.run('insights-client')


@pytest.fixture
def inventory_settings(rhcloud_sat_host):
    hostnames_setting = rhcloud_sat_host.update_setting('obfuscate_inventory_hostnames', False)
    ip_setting = rhcloud_sat_host.update_setting('obfuscate_inventory_ips', False)
    packages_setting = rhcloud_sat_host.update_setting('exclude_installed_packages', False)
    parameter_tags_setting = rhcloud_sat_host.update_setting('include_parameter_tags', False)
    yield
    rhcloud_sat_host.update_setting('obfuscate_inventory_hostnames', hostnames_setting)
    rhcloud_sat_host.update_setting('obfuscate_inventory_ips', ip_setting)
    rhcloud_sat_host.update_setting('exclude_installed_packages', packages_setting)
    rhcloud_sat_host.update_setting('include_parameter_tags', parameter_tags_setting)
