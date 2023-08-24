import pytest


@pytest.fixture(scope='module')
def rhcloud_manifest_org(module_target_sat, module_sca_manifest):
    """A module level fixture to get organization with manifest."""
    org = module_target_sat.api.Organization().create()
    module_target_sat.upload_manifest(org.id, module_sca_manifest.content)
    return org


@pytest.fixture(scope='module')
def organization_ak_setup(module_target_sat, rhcloud_manifest_org):
    """A module-level fixture to create an Activation key in module_org"""
    purpose_addons = "test-addon1, test-addon2"
    ak = module_target_sat.api.ActivationKey(
        content_view=rhcloud_manifest_org.default_content_view,
        organization=rhcloud_manifest_org,
        environment=module_target_sat.api.LifecycleEnvironment(id=rhcloud_manifest_org.library.id),
        purpose_addons=[purpose_addons],
        service_level='Self-Support',
        purpose_usage='test-usage',
        purpose_role='test-role',
        auto_attach=False,
    ).create()
    yield rhcloud_manifest_org, ak
    ak.delete()


@pytest.fixture(scope='module')
def rhcloud_registered_hosts(organization_ak_setup, mod_content_hosts, module_target_sat):
    """Fixture that registers content hosts to Satellite and Insights."""
    org, ak = organization_ak_setup
    for vm in mod_content_hosts:
        vm.configure_rhai_client(
            satellite=module_target_sat,
            activation_key=ak.name,
            org=org.label,
            rhel_distro=f"rhel{vm.os_version.major}",
        )
        assert vm.subscribed
    return mod_content_hosts


@pytest.fixture
def rhel_insights_vm(module_target_sat, organization_ak_setup, rhel_contenthost):
    """A function-level fixture to create rhel content host registered with insights."""
    # settings.supportability.content_hosts.rhel.versions
    org, ak = organization_ak_setup
    rhel_contenthost.configure_rex(satellite=module_target_sat, org=org, register=False)
    rhel_contenthost.configure_rhai_client(
        satellite=module_target_sat,
        activation_key=ak.name,
        org=org.label,
        rhel_distro=f"rhel{rhel_contenthost.os_version.major}",
    )
    yield rhel_contenthost
    # Delete host
    host = module_target_sat.api.Host().search(
        query={"search": f'name={rhel_contenthost.hostname}'}
    )[0]
    host.delete()
    assert not module_target_sat.api.Host().search(query={"search": f'name={host.name}'})


@pytest.fixture
def inventory_settings(module_target_sat):
    hostnames_setting = module_target_sat.update_setting('obfuscate_inventory_hostnames', False)
    ip_setting = module_target_sat.update_setting('obfuscate_inventory_ips', False)
    packages_setting = module_target_sat.update_setting('exclude_installed_packages', False)
    parameter_tags_setting = module_target_sat.update_setting('include_parameter_tags', False)
    yield
    module_target_sat.update_setting('obfuscate_inventory_hostnames', hostnames_setting)
    module_target_sat.update_setting('obfuscate_inventory_ips', ip_setting)
    module_target_sat.update_setting('exclude_installed_packages', packages_setting)
    module_target_sat.update_setting('include_parameter_tags', parameter_tags_setting)


@pytest.fixture(scope='module')
def rhcloud_capsule(module_capsule_host, module_target_sat, organization_ak_setup):
    """Configure the capsule instance with the satellite from settings.server.hostname"""
    org, ak = organization_ak_setup
    module_capsule_host.capsule_setup(sat_host=module_target_sat, enable_registration=True)
    capsule = module_target_sat.api.SmartProxy(name=module_capsule_host.hostname).search()[0].read()
    if org.id not in [organization.id for organization in capsule.organization]:
        capsule.organization.append(org)
        capsule.update(['organization'])
    yield module_capsule_host
