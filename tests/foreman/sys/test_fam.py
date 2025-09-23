"""Test class foreman ansible modules

:Requirement: Other

:CaseAutomation: Automated

:CaseImportance: High

:CaseComponent: AnsibleCollection

:Team: Rocket

"""

from broker import Broker
import pytest
import yaml

from robottelo.config import settings
from robottelo.constants import (
    FAM_IDM_TEST_PLAYBOOKS,
    FAM_MODULE_PATH,
    FAM_ROOT_DIR,
    FAM_TEST_LIBVIRT_PLAYBOOKS,
    FAM_TEST_PLAYBOOKS,
    FOREMAN_ANSIBLE_MODULES,
    HAMMER_CONFIG,
    RH_SAT_ROLES,
)
from robottelo.hosts import (
    IPAHost,
)
from robottelo.utils.installer import InstallerCommand


@pytest.fixture
def sync_roles(target_sat):
    """Sync all redhat.satellite roles and delete when finished
    Returns: A dict of the sync response and role names
    """
    roles = [f'redhat.satellite.{role}' for role in RH_SAT_ROLES]
    proxy_list = target_sat.cli.Proxy.list({'search': f'name={target_sat.hostname}'})
    proxy_id = proxy_list[0].get('id')
    sync = target_sat.cli.Ansible.roles_sync({'role-names': roles, 'proxy-id': proxy_id})
    yield {'task': sync, 'roles': roles}
    roles_list = target_sat.cli.Ansible.roles_list()
    for role in roles_list:
        role_id = role.get('id')
        target_sat.cli.Ansible.roles_delete({'id': role_id})


@pytest.fixture(scope='module')
def install_import_ansible_role(module_target_sat):
    """Installs and imports the thulium_drake.motd role used in the luna_hostgroup test playbook"""

    def create_fake_role(module_target_sat, role_name, role_metadata):
        base_dir = '/usr/share/ansible/roles'
        role_dir = f'{base_dir}/{role_name}'
        meta_dir = f'{role_dir}/meta'
        tasks_dir = f'{role_dir}/tasks'
        module_target_sat.execute(f'mkdir -p {meta_dir} {tasks_dir}')
        module_target_sat.put(
            yaml.safe_dump(role_metadata),
            f'{meta_dir}/main.yml',
            temp_file=True,
        )
        module_target_sat.put(
            '# NOOP',
            f'{tasks_dir}/main.yml',
            temp_file=True,
        )

    create_fake_role(
        module_target_sat,
        'thulium_drake.motd',
        {'galaxy_info': {'author': 'thulium_drake', 'role_name': 'motd'}},
    )

    proxy_id = module_target_sat.nailgun_smart_proxy.id
    module_target_sat.api.AnsibleRoles().sync(
        data={'proxy_id': proxy_id, 'role_names': 'thulium_drake.motd'}
    )


def common_fam_setup(satellite):
    satellite.put(
        settings.fam.compute_profile.to_yaml(),
        f'{FAM_ROOT_DIR}/tests/test_playbooks/vars/compute_profile.yml',
        temp_file=True,
    )

    # Create fake galaxy.yml to make Makefile happy.
    # The data in the file is unused, but not being able to load it produces errors in the
    # logs and is confusing when searching for an actual problem during testing.
    satellite.put(
        yaml.safe_dump({'name': 'satellite', 'namespace': 'redhat', 'version': '1.0.0'}),
        f'{FAM_ROOT_DIR}/galaxy.yml',
        temp_file=True,
    )

    # Edit Makefile to not try to rebuild the collection when tests run
    satellite.execute(f"sed -i '/^live/ s/$(MANIFEST)//' {FAM_ROOT_DIR}/Makefile")

    # Edit Makefile to use passed-in pytest
    # Can be removed once https://github.com/theforeman/foreman-ansible-modules/pull/1788
    # is present in all relevant branches
    satellite.execute(f"sed -i '/test_crud/ s/pytest/$(PYTEST_COMMAND)/' {FAM_ROOT_DIR}/Makefile")

    # Edit inventory configurations
    satellite.execute(
        f"sed -i '/url/ s#http.*#https://localhost#' {FAM_ROOT_DIR}/tests/inventory/*.foreman.yml {FAM_ROOT_DIR}/tests/test_playbooks/vars/inventory.yml"
    )
    satellite.execute(
        f"sed -i '/inventory_use_container/ s#true#false#' {FAM_ROOT_DIR}/tests/test_playbooks/vars/inventory.yml"
    )

    # Edit content_import tests
    # They need to extract data on the Foreman/Satellite machine and use "hosts: foreman" for that
    # As we're running locally, we can use "hosts: localhost" instead
    satellite.execute(
        f"sed -i '/hosts:/ s/foreman/localhost/' {FAM_ROOT_DIR}/tests/test_playbooks/content_import_*.yml"
    )


@pytest.fixture(scope='module')
def setup_fam(
    module_target_sat, module_sca_manifest, install_import_ansible_role, module_capsule_configured
):
    # Execute AAP WF for FAM setup
    Broker().execute(workflow='fam-test-setup', source_vm=module_target_sat.name)

    # Update the settings to point to our Capsule
    settings.set('fam.server.foreman_proxy', module_capsule_configured.hostname)

    # Copy config files to the Satellite
    module_target_sat.put(
        settings.fam.server.to_yaml(),
        f'{FAM_ROOT_DIR}/tests/test_playbooks/vars/server.yml',
        temp_file=True,
    )

    common_fam_setup(module_target_sat)

    # Edit repos used in tests
    # Until https://github.com/theforeman/foreman-ansible-modules/pull/1899 is in
    module_target_sat.execute(
        f"sed -i 's#https://repos.fedorapeople.org/pulp/pulp/demo_repos/zoo/#https://fixtures.pulpproject.org/rpm-signed/#' {FAM_ROOT_DIR}/tests/test_playbooks/*.yml"
    )

    # Upload manifest to test playbooks directory
    module_target_sat.put(str(module_sca_manifest.path), str(module_sca_manifest.name))
    module_target_sat.execute(
        f'mv {module_sca_manifest.name} {FAM_ROOT_DIR}/tests/test_playbooks/data'
    )
    config_file = f'{FAM_ROOT_DIR}/tests/test_playbooks/vars/server.yml'
    module_target_sat.execute(
        f'''sed -i 's|subscription_manifest_path:.*|subscription_manifest_path: "data/{module_sca_manifest.name}"|g' {config_file}'''
    )

    def create_fake_module(module_target_sat, module_name, module_classes):
        base_dir = '/etc/puppetlabs/code/environments/production/modules'
        module_dir = f'{base_dir}/{module_name}'
        manifest_dir = f'{module_dir}/manifests'
        module_target_sat.execute(f'mkdir -p {manifest_dir}')
        for module_class in module_classes:
            if isinstance(module_class, str):
                module_code = '(){}'
            else:
                module_class, module_code = module_class
            full_class = module_name if module_class == 'init' else f'{module_name}::{module_class}'
            module_target_sat.put(
                f'class {full_class}{module_code}',
                f'{manifest_dir}/{module_class}.pp',
                temp_file=True,
            )

    create_fake_module(
        module_target_sat,
        'ntp',
        [('init', '($logfile, $config_dir, $servers, $burst, $stepout){}'), 'config'],
    )

    create_fake_module(
        module_target_sat,
        'prometheus',
        ['init', 'haproxy_exporter', 'redis_exporter', 'statsd_exporter'],
    )

    smart_proxy = module_target_sat.nailgun_smart_proxy.read()
    smart_proxy.import_puppetclasses()

    create_fake_module(module_target_sat, 'fakemodule', ['init'])


@pytest.fixture(scope='module')
def setup_fam_with_idm(idm_sat, module_sca_manifest):
    # Execute AAP WF for FAM setup
    Broker().execute(workflow='fam-test-setup', source_vm=idm_sat.name)

    # Modify and copy config files to the Satellite
    idm_fam_settings = settings.fam.server.copy()
    # Replace hostname in the settings
    for k, v in idm_fam_settings.items():
        if isinstance(v, str):
            idm_fam_settings[k] = v.replace(settings.server.hostname, idm_sat.hostname)
    # Remove username and password as they are not used in IDM
    idm_fam_settings['foreman_username'] = "{{ omit }}"
    idm_fam_settings['satellite_username'] = "{{ omit }}"
    idm_fam_settings['foreman_password'] = "{{ omit }}"
    idm_fam_settings['satellite_password'] = "{{ omit }}"

    idm_sat.put(
        idm_fam_settings.to_yaml(),
        f'{FAM_ROOT_DIR}/tests/test_playbooks/vars/server.yml',
        temp_file=True,
    )

    common_fam_setup(idm_sat)

    # Upload manifest to test playbooks directory
    idm_sat.put(str(module_sca_manifest.path), str(module_sca_manifest.name))
    idm_sat.execute(f'mv {module_sca_manifest.name} {FAM_ROOT_DIR}/tests/test_playbooks/data')
    config_file = f'{FAM_ROOT_DIR}/tests/test_playbooks/vars/server.yml'
    idm_sat.execute(
        f'''sed -i 's|subscription_manifest_path:.*|subscription_manifest_path: "data/{module_sca_manifest.name}"|g' {config_file}'''
    )


@pytest.fixture(scope='module')
def idm_sat(satellite_factory, ad_data):
    """Yields a Satellite enrolled into IDM."""
    new_sat = satellite_factory()
    new_sat.enable_satellite_ipv6_http_proxy()
    new_sat.register_to_cdn()
    ipa_host = IPAHost(new_sat)
    ipa_host.enroll_idm_and_configure_external_auth()
    new_sat.install(InstallerCommand('foreman-ipa-authentication-api true'))
    # Installs requests-gssapi package to be able to use GSSAPI authentication
    new_sat.execute('yum -y --disableplugin=foreman-protector install python3-requests-gssapi')
    # Configures hammer to use sessions and negotiate auth
    new_sat.execute(f"sed -i '/:username.*/d' {HAMMER_CONFIG}")
    new_sat.execute(f"sed -i '/:password.*/d' {HAMMER_CONFIG}")
    new_sat.execute(f"sed -i '/:default_auth_type.*/d' {HAMMER_CONFIG}")
    new_sat.execute(f"sed -i '/:use_sessions.*/d' {HAMMER_CONFIG}")
    new_sat.execute(f"echo '  :use_sessions: true' >> {HAMMER_CONFIG}")
    new_sat.execute(f"echo '  :default_auth_type: Negotiate_Auth' >> {HAMMER_CONFIG}")
    # Authenticate to Satellite using IPA
    with new_sat.omit_credentials():
        new_sat.execute(f'echo {settings.ipa.password} | kinit {settings.ipa.user}')
        new_sat.cli.AuthLogin.negotiate()
    # Set user as admin
    user = new_sat.api.User().search(query={'search': f'login={settings.ipa.user.lower()}'})[0]
    user.admin = True
    user.update()
    yield new_sat
    ipa_host.disenroll_idm()
    new_sat.unregister()
    new_sat.teardown()
    Broker(hosts=[new_sat]).checkin()


@pytest.mark.pit_server
@pytest.mark.run_in_one_thread
def test_positive_ansible_modules_installation(target_sat):
    """Foreman ansible modules installation test

    :id: 553a927e-2665-4227-8542-0258d7b1ccc4

    :expectedresults: ansible-collection-redhat-satellite package is
        available and supported modules are contained
    """
    # list installed modules
    result = target_sat.execute(f'ls {FAM_MODULE_PATH} | grep .py$ | sed "s/.[^.]*$//"')
    assert result.status == 0
    installed_modules = result.stdout.split('\n')
    installed_modules.remove('')
    # see help for installed modules
    for module_name in installed_modules:
        result = target_sat.execute(f'ansible-doc redhat.satellite.{module_name} -s')
        assert result.status == 0
        doc_name = result.stdout.split('\n')[1].lstrip()[:-1]
        assert doc_name == module_name
    # check installed modules against the expected list
    assert sorted(FOREMAN_ANSIBLE_MODULES) == sorted(installed_modules)

    # check installed modules are tested
    untested_modules = set(installed_modules) - set(FAM_TEST_PLAYBOOKS)
    assert untested_modules == set(), (
        f'The following modules have no tests: {", ".join(untested_modules)}'
    )


@pytest.mark.e2e
@pytest.mark.pit_server
def test_positive_import_run_roles(sync_roles, target_sat):
    """Import a FAM role and run the role on the Satellite

    :id: d3379fd3-b847-43ce-a51f-c02170e7b267

    :expectedresults: fam roles import and run successfully
    """
    roles = sync_roles.get('roles')
    target_sat.cli.Host.ansible_roles_assign({'ansible-roles': roles, 'name': target_sat.hostname})
    play = target_sat.cli.Host.ansible_roles_play({'name': target_sat.hostname})
    assert 'Ansible roles are being played' in play[0]['message']


@pytest.mark.e2e
@pytest.mark.parametrize('ansible_module', FAM_TEST_PLAYBOOKS)
def test_positive_run_modules_and_roles(module_target_sat, setup_fam, ansible_module):
    """Run all FAM modules and roles on the Satellite

    :id: b595756f-627c-44ea-b738-aa17ff5b1d39

    :expectedresults: All modules and roles run successfully
    """
    common_test_positive_run_modules_and_roles(module_target_sat, ansible_module)


@pytest.mark.destructive
@pytest.mark.parametrize('ansible_module', FAM_IDM_TEST_PLAYBOOKS)
def test_positive_run_modules_and_roles_kerberos_auth(idm_sat, setup_fam_with_idm, ansible_module):
    """Run limited set of modules and roles on a Satellite with Kerberos authentication

    :id: c6ac4c73-fdd2-4617-87d2-ca41fa8946ff

    :expectedresults: All modules and roles run successfully
    """
    common_test_positive_run_modules_and_roles(idm_sat, ansible_module, ["SATELLITE_USE_GSSAPI=1"])


def common_test_positive_run_modules_and_roles(satellite, ansible_module, extra_env=None):
    """Common part of test_positive_run_modules_and_roles and test_positive_run_modules_and_roles_kerberos_auth"""
    # Skip FAM tests w/o proper setups
    if (
        ansible_module
        in [
            "host_errata_info",  # this test requires a host with non-applied errata
            "host_power",  # this test tries to power off non-existent VM
            "realm",  # realm feature is not set up on Capsule
            "smart_proxy",  # the tests try to create a new proxy, which doesn't work for Katello/Satellite, only plain Foreman
        ]
    ):
        pytest.skip(f"{ansible_module} module test lacks proper setup")

    # Setup provisioning resources
    if ansible_module in FAM_TEST_LIBVIRT_PLAYBOOKS:
        satellite.configure_libvirt_cr()

    env = [
        'NO_COLOR=1',
        'PYTEST_DISABLE_PLUGIN_AUTOLOAD=1',
        'ANSIBLE_HOST_PATTERN_MISMATCH=ignore',
    ]
    if extra_env is not None:
        env.extend(extra_env)

    if not satellite.network_type.has_ipv4:
        if ansible_module in ['redhat_manifest']:
            env.append(f'HTTPS_PROXY={settings.http_proxy.http_proxy_ipv6_url}')

        satellite.enable_satellite_http_proxy()

    # Execute test_playbook
    result = satellite.execute(
        f'{" ".join(env)} make --directory {FAM_ROOT_DIR} livetest_{ansible_module} PYTHON_COMMAND="python3" PYTEST_COMMAND="pytest-3.12"',
        timeout="30m",
    )
    assert result.status == 0, f"{result.status=}\n{result.stdout=}\n{result.stderr=}"


@pytest.mark.e2e
@pytest.mark.parametrize('ansible_module', ['inventory_plugin', 'inventory_plugin_ansible'])
def test_positive_run_inventory(module_target_sat, setup_fam, ansible_module):
    """Run FAM inventory on the Satellite

    :id: 6160216d-c460-437c-b440-1d283efbac70

    :expectedresults: All inventories run successfully
    """
    # Execute test_playbook
    result = module_target_sat.execute(
        f'cd {FAM_ROOT_DIR} && NO_COLOR=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest-3.12 tests/test_crud.py::test_inventory[{ansible_module}]'
    )
    assert result.status == 0, f"{result.status=}\n{result.stdout=}\n{result.stderr=}"
