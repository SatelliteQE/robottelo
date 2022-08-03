import pytest
from broker import Broker

from robottelo.config import settings
from robottelo.constants import DEFAULT_SUBSCRIPTION_NAME


@pytest.fixture(scope='module')
def rhcloud_sat_host(satellite_factory):
    """A module level fixture that provides a Satellite based on config settings"""
    new_sat = satellite_factory()
    yield new_sat
    new_sat.teardown()
    Broker(hosts=[new_sat]).checkin()


@pytest.fixture(scope='module')
def rhcloud_manifest_org(rhcloud_sat_host):
    """A module level fixture to get organization with manifest."""
    org = rhcloud_sat_host.api.Organization().create()
    manifests_path = rhcloud_sat_host.download_file(file_url=settings.fake_manifest.url['default'])[
        0
    ]
    rhcloud_sat_host.cli.Subscription.upload({'file': manifests_path, 'organization-id': org.id})
    return org


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
def rhcloud_registered_hosts(organization_ak_setup, mod_content_hosts, rhcloud_sat_host):
    """Fixture that registers content hosts to Satellite and Insights."""
    org, ak = organization_ak_setup
    for vm in mod_content_hosts:
        vm.configure_rhai_client(
            satellite=rhcloud_sat_host,
            activation_key=ak.name,
            org=org.label,
            rhel_distro=f"rhel{vm.os_version.major}",
        )
        assert vm.subscribed
    return mod_content_hosts


@pytest.fixture
def rhel_insights_vm(rhcloud_sat_host, organization_ak_setup, rhel_contenthost):
    """A module-level fixture to create rhel content host registered with insights."""
    # settings.supportability.content_hosts.rhel.versions
    org, ak = organization_ak_setup
    rhel_contenthost.configure_rex(satellite=rhcloud_sat_host, org=org, register=False)
    rhel_contenthost.configure_rhai_client(
        satellite=rhcloud_sat_host,
        activation_key=ak.name,
        org=org.label,
        rhel_distro=f"rhel{rhel_contenthost.os_version.major}",
    )
    yield rhel_contenthost


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
