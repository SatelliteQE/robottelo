"""Smoke tests to check installation health

:Requirement: Installation

:CaseAutomation: Automated

:CaseComponent: Installation

:Team: Platform

:CaseImportance: Critical

"""

import pytest
import requests
import yaml

from robottelo import ssh
from robottelo.config import settings
from robottelo.constants import DEFAULT_ARCHITECTURE, FOREMAN_SETTINGS_YML, PRDS, REPOS, REPOSET
from robottelo.utils.installer import InstallerCommand
from robottelo.utils.issue_handlers import is_open
from robottelo.utils.ohsnap import dogfood_repository

SATELLITE_SERVICES = [
    'dynflow-sidekiq@orchestrator',
    'dynflow-sidekiq@worker-1',
    'dynflow-sidekiq@worker-hosts-queue-1',
    'foreman-proxy',
    'foreman',
    'httpd',
    'postgresql',
    'pulpcore-api',
    'pulpcore-content',
    'pulpcore-worker@*',
    'tomcat',
]

DOWNSTREAM_MODULES = {
    'apache::mod::status',
    'certs',
    'foreman',
    'foreman::cli',
    'foreman::cli::ansible',
    'foreman::cli::azure',
    'foreman::cli::google',
    'foreman::cli::katello',
    'foreman::cli::kubevirt',
    'foreman::cli::puppet',
    'foreman::cli::remote_execution',
    'foreman::cli::virt_who_configure',
    'foreman::cli::webhooks',
    'foreman::compute::ec2',
    'foreman::compute::libvirt',
    'foreman::compute::openstack',
    'foreman::compute::ovirt',
    'foreman::compute::vmware',
    'foreman::plugin::ansible',
    'foreman::plugin::azure',
    'foreman::plugin::bootdisk',
    'foreman::plugin::discovery',
    'foreman::plugin::google',
    'foreman::plugin::kubevirt',
    'foreman::plugin::leapp',
    'foreman::plugin::openscap',
    'foreman::plugin::puppet',
    'foreman::plugin::remote_execution',
    'foreman::plugin::remote_execution::cockpit',
    'foreman::plugin::rh_cloud',
    'foreman::plugin::tasks',
    'foreman::plugin::templates',
    'foreman::plugin::virt_who_configure',
    'foreman::plugin::webhooks',
    'foreman_proxy',
    'foreman_proxy::plugin::ansible',
    'foreman_proxy::plugin::dhcp::infoblox',
    'foreman_proxy::plugin::dhcp::remote_isc',
    'foreman_proxy::plugin::discovery',
    'foreman_proxy::plugin::dns::infoblox',
    'foreman_proxy::plugin::openscap',
    'foreman_proxy::plugin::remote_execution::script',
    'foreman_proxy::plugin::shellhooks',
    'foreman_proxy_content',
    'katello',
    'puppet',
}


def extract_help(filter='params'):
    """Generator function to extract satellite installer params and sections from lines
    of help text. In general lst is cmd.stdout, e.g., a list of strings representing host stdout.

    :param string filter: Filter `sections` or `params` in full help, default is params
    :return: generator with params or sections depends on filter parameter
    """
    stdout = ssh.command('satellite-installer --full-help').stdout
    for line in stdout.splitlines() or []:
        line = line.strip()
        if filter == 'sections':
            if line.startswith('= '):
                yield line
        else:
            first_2_tokens = line.split()[:2]
            for token in first_2_tokens:
                if token[0] == '-':
                    yield token.replace(',', '')


def common_sat_install_assertions(satellite):
    sat_version = 'stream' if satellite.is_stream else satellite.version
    assert settings.server.version.release == sat_version

    # no errors/failures in journald
    result = satellite.execute(
        r'journalctl --quiet --no-pager --boot --priority err -u "dynflow-sidekiq*" -u "foreman-proxy" -u "foreman" -u "httpd" -u "postgresql" -u "pulpcore-api" -u "pulpcore-content" -u "pulpcore-worker*" -u "redis" -u "tomcat"'
    )
    assert len(result.stdout) == 0
    # no errors in /var/log/foreman/production.log
    result = satellite.execute(r'grep --context=100 -E "\[E\|" /var/log/foreman/production.log')
    if not is_open('SAT-21086'):
        assert len(result.stdout) == 0
    # no errors/failures in /var/log/foreman-installer/satellite.log
    result = satellite.execute(
        r'grep "\[ERROR" --context=100 /var/log/foreman-installer/satellite.log'
    )
    assert len(result.stdout) == 0
    # no errors/failures in /var/log/httpd/*
    result = satellite.execute(r'grep -iR "error" /var/log/httpd/*')
    assert len(result.stdout) == 0
    # no errors/failures in /var/log/candlepin/*
    result = satellite.execute(r'grep -iR "error" /var/log/candlepin/*')
    assert len(result.stdout) == 0

    httpd_log = satellite.execute('journalctl --unit=httpd')
    assert "WARNING" not in httpd_log.stdout

    result = satellite.cli.Health.check()
    assert 'FAIL' not in result.stdout


def install_satellite(satellite, installer_args, enable_fapolicyd=False):
    # Register for RHEL8 repos, get Ohsnap repofile, and enable and download satellite
    satellite.register_to_cdn()
    if settings.server.version.source == 'nightly':
        satellite.create_custom_repos(
            satellite_repo=settings.repos.satellite_repo,
            satmaintenance_repo=settings.repos.satmaintenance_repo,
        )
    else:
        satellite.download_repofile(
            product='satellite',
            release=settings.server.version.release,
            snap=settings.server.version.snap,
        )
    if enable_fapolicyd:
        if satellite.execute('rpm -q satellite-maintain').status == 0:
            # Installing the rpm on existing sat needs sat-maintain perms
            cmmd = 'satellite-maintain packages install fapolicyd -y'
        else:
            cmmd = 'dnf -y install fapolicyd'
        assert satellite.execute(f'{cmmd} && systemctl enable --now fapolicyd').status == 0
    satellite.install_satellite_or_capsule_package()
    if enable_fapolicyd:
        assert satellite.execute('rpm -q foreman-fapolicyd').status == 0
        assert satellite.execute('rpm -q foreman-proxy-fapolicyd').status == 0
    # Configure Satellite firewall to open communication
    satellite.execute(
        'firewall-cmd --permanent --add-service RH-Satellite-6 && firewall-cmd --reload'
    )
    # Install Satellite
    satellite.execute(
        InstallerCommand(installer_args=installer_args).get_command(),
        timeout='30m',
    )


def setup_capsule_repos(satellite, capsule_host, org, ak):
    """
    Enables repositories that are necessary to install capsule
    1. Enable RHEL repositories based on configuration
    2. Enable capsule repositories based on configuration
    3. Synchonize repositories
    """
    # List of sync tasks - all repos will be synced asynchronously
    sync_tasks = []

    # Enable and sync RHEL BaseOS and AppStream repos
    if settings.robottelo.rhel_source == "internal":
        # Configure internal sources as custom repositories
        product_rhel = satellite.api.Product(organization=org.id).create()
        for repourl in settings.repos.get(f'rhel{capsule_host.os_version.major}_os').values():
            repo = satellite.api.Repository(
                organization=org.id, product=product_rhel, content_type='yum', url=repourl
            ).create()
            # custom repos need to be explicitly enabled
            ak.content_override(
                data={
                    'content_overrides': [
                        {
                            'content_label': '_'.join([org.label, product_rhel.label, repo.label]),
                            'value': '1',
                        }
                    ]
                }
            )
    else:
        # use AppStream and BaseOS from CDN
        for rh_repo_key in [
            f'rhel{capsule_host.os_version.major}_bos',
            f'rhel{capsule_host.os_version.major}_aps',
        ]:
            satellite.api_factory.enable_rhrepo_and_fetchid(
                basearch=DEFAULT_ARCHITECTURE,
                org_id=org.id,
                product=PRDS[f'rhel{capsule_host.os_version.major}'],
                repo=REPOS[rh_repo_key]['name'],
                reposet=REPOSET[rh_repo_key],
                releasever=REPOS[rh_repo_key]['releasever'],
            )
        product_rhel = satellite.api.Product(
            name=PRDS[f'rhel{capsule_host.os_version.major}'], organization=org.id
        ).search()[0]
    sync_tasks.append(satellite.api.Product(id=product_rhel.id).sync(synchronous=False))

    # Enable and sync Capsule repos
    if settings.capsule.version.source == "ga":
        # enable Capsule repos from CDN
        for repo in capsule_host.CAPSULE_CDN_REPOS.values():
            reposet = satellite.api.RepositorySet(organization=org.id).search(
                query={'search': repo}
            )[0]
            reposet.enable()
            # repos need to be explicitly enabled in AK
            ak.content_override(
                data={
                    'content_overrides': [
                        {
                            'content_label': reposet.label,
                            'value': '1',
                        }
                    ]
                }
            )
            sync_tasks.append(satellite.api.Product(id=reposet.product.id).sync(synchronous=False))
    else:
        # configure internal source as custom repos
        product_capsule = satellite.api.Product(organization=org.id).create()
        for repo_variant, repo_default_url in [
            ('capsule', 'capsule_repo'),
            ('maintenance', 'satmaintenance_repo'),
        ]:
            if settings.capsule.version.source == 'nightly':
                repo_url = getattr(settings.repos, repo_default_url)
            else:
                repo_url = dogfood_repository(
                    ohsnap=settings.ohsnap,
                    repo=repo_variant,
                    product="capsule",
                    release=settings.capsule.version.release,
                    os_release=capsule_host.os_version.major,
                    snap=settings.capsule.version.snap,
                ).baseurl
            repo = satellite.api.Repository(
                organization=org.id,
                product=product_capsule,
                content_type='yum',
                url=repo_url,
            ).create()

            # custom repos need to be explicitly enabled
            ak.content_override(
                data={
                    'content_overrides': [
                        {
                            'content_label': '_'.join(
                                [org.label, product_capsule.label, repo.label]
                            ),
                            'value': '1',
                        }
                    ]
                }
            )
        sync_tasks.append(satellite.api.Product(id=product_capsule.id).sync(synchronous=False))

    # Wait for asynchronous sync tasks
    satellite.wait_for_tasks(
        search_query=(f'id ^ "{",".join(task["id"] for task in sync_tasks)}"'),
        poll_timeout=1800,
    )


@pytest.fixture(scope='module')
def sat_default_install(module_sat_ready_rhels):
    """Install Satellite with default options"""
    installer_args = [
        'scenario satellite',
        f'foreman-initial-admin-password {settings.server.admin_password}',
    ]
    sat = module_sat_ready_rhels.pop()
    install_satellite(sat, installer_args)
    sat.enable_ipv6_http_proxy()
    return sat


@pytest.fixture(scope='module')
def sat_fapolicyd_install(module_sat_ready_rhels):
    """Install Satellite with default options and fapolicyd enabled"""
    installer_args = [
        'scenario satellite',
        f'foreman-initial-admin-password {settings.server.admin_password}',
    ]
    sat = module_sat_ready_rhels.pop()
    install_satellite(sat, installer_args, enable_fapolicyd=True)
    sat.enable_ipv6_http_proxy()
    return sat


@pytest.fixture(scope='module')
def sat_non_default_install(module_sat_ready_rhels):
    """Provides fapolicyd enabled Satellite with various options"""
    installer_args = [
        'scenario satellite',
        f'foreman-initial-admin-password {settings.server.admin_password}',
        'foreman-rails-cache-store type:file',
        'foreman-proxy-content-pulpcore-hide-guarded-distributions false',
        'enable-foreman-plugin-discovery',
        'foreman-proxy-plugin-discovery-install-images true',
    ]
    sat = module_sat_ready_rhels.pop()
    install_satellite(sat, installer_args, enable_fapolicyd=True)
    sat.enable_ipv6_http_proxy()
    sat.execute('dnf -y --disableplugin=foreman-protector install foreman-discovery-image')
    return sat


@pytest.mark.e2e
@pytest.mark.tier1
@pytest.mark.pit_server
@pytest.mark.build_sanity
@pytest.mark.parametrize(
    'setting_update',
    [f'http_proxy={settings.http_proxy.un_auth_proxy_url}'],
    indirect=True,
    ids=["un_auth_proxy"],
)
def test_capsule_installation(
    sat_fapolicyd_install, cap_ready_rhel, module_sca_manifest, setting_update
):
    """Run a basic Capsule installation with fapolicyd

    :id: 64fa85b6-96e6-4fea-bea4-a30539d59e65

    :steps:
        1. Use Satellite with fapolicyd enabled
        2. Configure RHEL and Capsule repos on Satellite
        3. Register Capsule machine to consume Satellite content
        4. Install and enable fapolicyd
        5. Install and setup capsule

    :expectedresults:
        1. Capsule is installed and setup correctly
        2. no unexpected errors in logs
        3. health check runs successfully

    :CaseImportance: Critical

    :Verifies: SAT-24520

    :BZ: 1984400

    :customerscenario: true
    """
    # Create testing organization
    org = sat_fapolicyd_install.api.Organization().create()

    # Unregister capsule in case it's registered to CDN
    cap_ready_rhel.unregister()

    # Add a manifest to the Satellite
    sat_fapolicyd_install.upload_manifest(org.id, module_sca_manifest.content)
    # Create capsule certs and activation key
    file, _, cmd_args = sat_fapolicyd_install.capsule_certs_generate(cap_ready_rhel)
    sat_fapolicyd_install.session.remote_copy(file, cap_ready_rhel)
    ak = sat_fapolicyd_install.api.ActivationKey(
        organization=org, environment=org.library, content_view=org.default_content_view
    ).create()

    setup_capsule_repos(sat_fapolicyd_install, cap_ready_rhel, org, ak)

    cap_ready_rhel.register(org, None, ak.name, sat_fapolicyd_install)

    # Install (enable) fapolicyd
    assert (
        cap_ready_rhel.execute(
            'dnf -y install fapolicyd && systemctl enable --now fapolicyd'
        ).status
        == 0
    )

    # Install Capsule package
    cap_ready_rhel.install_satellite_or_capsule_package()
    assert cap_ready_rhel.execute('rpm -q foreman-proxy-fapolicyd').status == 0

    # Setup Capsule
    cap_ready_rhel.install(cmd_args)

    assert sat_fapolicyd_install.api.Capsule().search(
        query={'search': f'name={cap_ready_rhel.hostname}'}
    )[0]

    # no errors/failures in journald
    result = cap_ready_rhel.execute(
        r'journalctl --quiet --no-pager --boot --priority err -u foreman-proxy -u httpd -u postgresql -u pulpcore-api -u pulpcore-content -u pulpcore-worker* -u redis'
    )
    assert len(result.stdout) == 0
    # no errors/failures /var/log/foreman-installer/satellite.log
    result = cap_ready_rhel.execute(
        r'grep "\[ERROR" --context=100 /var/log/foreman-installer/satellite.log'
    )
    assert len(result.stdout) == 0
    # no errors/failures /var/log/foreman-installer/capsule.log
    result = cap_ready_rhel.execute(
        r'grep "\[ERROR" --context=100 /var/log/foreman-installer/capsule.log'
    )
    assert len(result.stdout) == 0
    # no errors/failures in /var/log/httpd/*
    result = cap_ready_rhel.execute(r'grep -iR "error" /var/log/httpd/*')
    assert len(result.stdout) == 0
    # no errors/failures in /var/log/foreman-proxy/*
    result = cap_ready_rhel.execute(r'grep -iR "error" /var/log/foreman-proxy/*')
    assert len(result.stdout) == 0

    result = cap_ready_rhel.cli.Health.check()
    assert 'FAIL' not in result.stdout

    # Verify foreman-proxy-content-reverse-proxy and port 8443 are disabled on default installation
    help_result = cap_ready_rhel.execute(
        "satellite-installer --full-help | grep foreman-proxy-content-reverse-proxy"
    )
    assert "Add reverse proxy to the parent (current: false)" in help_result.stdout
    port_result = cap_ready_rhel.execute("ss -tuln | grep 8443")
    assert not port_result.stdout


@pytest.mark.e2e
@pytest.mark.tier1
def test_foreman_rails_cache_store(sat_non_default_install):
    """Test foreman-rails-cache-store option

    :id: 379a2fe8-1085-4a7f-8ac3-24c421412f12

    :steps:
        1. Install Satellite with option foreman-rails-cache-store type:file
        2. Verify that foreman-redis package is not installed.
        3. Check /etc/foreman/settings.yaml

    :CaseImportance: Medium

    :customerscenario: true

    :BZ: 2063717, 2165092, 2244370
    """
    # Verify foreman-rails-cache-store option works
    assert sat_non_default_install.execute('rpm -q foreman-redis').status == 1
    settings_file = sat_non_default_install.load_remote_yaml_file(FOREMAN_SETTINGS_YML)
    assert settings_file.rails_cache_store.type == 'file'


@pytest.mark.e2e
@pytest.mark.tier1
def test_content_guarded_distributions_option(
    sat_default_install, sat_non_default_install, module_sca_manifest
):
    """Verify foreman-proxy-content-pulpcore-hide-guarded-distributions option works

    :id: a9ceefbc-fc2d-415e-9461-1811fabc63dc

    :steps:
        1. Install Satellite.
        2. Verify that no content is listed on https://sat-fqdn/pulp/content/
            with default Satellite installation.
        3. Verify that content is not downloadable when content guard setting is disabled.

    :expectedresults:
        1. no content is listed on https://sat-fqdn/pulp/content/

    :CaseImportance: Medium

    :customerscenario: true

    :BZ: 2063717, 2088559
    """
    # Verify that no content is listed on https://sat-fqdn/pulp/content/.
    result = requests.get(f'https://{sat_default_install.hostname}/pulp/content/', verify=False)
    assert 'Default_Organization' not in result.text
    # Verify that content is not downloadable when content guard setting is disabled.
    org = sat_non_default_install.api.Organization().create()
    sat_non_default_install.upload_manifest(org.id, module_sca_manifest.content)
    # sync ansible repo
    product = sat_non_default_install.api.Product(name=PRDS['rhae'], organization=org.id).search()[
        0
    ]
    r_set = sat_non_default_install.api.RepositorySet(
        name=REPOSET['rhae2.9_el8'], product=product
    ).search()[0]
    r_set.enable(
        data={
            'basearch': 'x86_64',
            'name': REPOSET['rhae2.9_el8'],
            'organization-id': org.id,
            'product_id': product.id,
            'releasever': '8',
        }
    )
    rh_repo = sat_non_default_install.api.Repository(name=REPOS['rhae2.9_el8']['name']).search(
        query={'organization_id': org.id}
    )[0]
    rh_repo.sync()
    assert (
        "403"
        in sat_non_default_install.execute(
            f'curl https://{sat_non_default_install.hostname}/pulp/content/{org.label}'
            f'/Library/content/dist/layered/rhel8/x86_64/ansible/2.9/os/'
        ).stdout
    )


@pytest.mark.upgrade
@pytest.mark.tier1
def test_positive_selinux_foreman_module(target_sat):
    """Check if SELinux foreman module is installed on Satellite

    :id: a0736b3a-3d42-4a09-a11a-28c1d58214a5

    :steps:
        1. Check "foreman-selinux" package availability on satellite.
        2. Check SELinux foreman module on satellite.

    :expectedresults: Foreman RPM and SELinux module are both present on the satellite
    """
    rpm_result = target_sat.execute('rpm -q foreman-selinux')
    assert rpm_result.status == 0

    semodule_result = target_sat.execute('semodule -l | grep foreman')
    assert semodule_result.status == 0


@pytest.mark.upgrade
@pytest.mark.tier1
@pytest.mark.parametrize('service', SATELLITE_SERVICES)
def test_positive_check_installer_service_running(target_sat, service):
    """Check if a service is running

    :id: 5389c174-7ab1-4e9d-b2aa-66d80fd6dc5f

    :steps:
        1. Verify a service is active with systemctl is-active

    :expectedresults: The service is active

    :CaseImportance: Medium
    """
    is_active = target_sat.execute(f'systemctl is-active {service}')
    status = target_sat.execute(f'systemctl status {service}')
    assert is_active.status == 0, status.stdout


@pytest.mark.upgrade
@pytest.mark.tier1
def test_positive_check_installer_hammer_ping(target_sat):
    """Check if hammer ping reports all services as ok

    :id: 85fd4388-6d94-42f5-bed2-24be38e9f104

    :steps:
        1. Run the 'hammer ping' command on satellite.

    :BZ: 1964394

    :customerscenario: true

    :expectedresults: All services are active (running)
    """
    # check status reported by hammer ping command
    result = target_sat.execute('hammer ping')
    assert result.status == 0
    for line in result.stdout.split('\n'):
        if 'Status' in line:
            assert 'ok' in line


@pytest.mark.upgrade
@pytest.mark.tier1
@pytest.mark.build_sanity
def test_installer_modules_check(target_sat):
    """Look for changes in installer modules

    :id: a51d3b9f-f347-4a96-a31a-770349db08c7

    :steps:
        1. Parse satellite installer modules

    :expectedresults: Ensure the keys for all modules are in the file
    """
    cat_cmd = target_sat.execute('cat /etc/foreman-installer/scenarios.d/satellite-answers.yaml')
    sat_answers = yaml.safe_load(cat_cmd.stdout)

    assert set(sat_answers) == DOWNSTREAM_MODULES


@pytest.mark.stubbed
@pytest.mark.tier3
def test_satellite_installation_on_ipv6():
    """
    Check the satellite installation on ipv6 machine.

    :id: 24fa5ef0-1673-427c-82ab-740758683cff

    :steps:
        1. Install satellite on ipv6 machine.

    :expectedresults:
        1: Installation should be successful.
        2: After installation, All the services should be up and running.
        3. Status of hammer ping should be ok.
        4: Satellite service restart should work.
        5: After system reboot all the services comes to up state.

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
@pytest.mark.tier3
def test_capsule_installation_on_ipv6():
    """
    Check the capsule installation over ipv6 machine

    :id: 75341e29-342f-41fc-aaa8-cda013b7dfa1

    :steps:
        1. Install capsule on ipv6 machine.

    :expectedresults:
        1. Capsule installation should be successful.
        2. After installation, All the Services should be up and running.
        3. Satellite service restart should work.
        4. After system reboot all the services come to up state.

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
@pytest.mark.tier3
def test_installer_check_on_ipv6():
    """
    Check the satellite-installer command execution with tuning options and updated config file.

    :id: 411bbffb-027f-4df0-8566-1719d1d0651a

    :steps:
        1. Install satellite on ipv6 machine
        2. Trigger the satellite-installer command with "--tuning medium" flag.
        3. Update the custom-hira.yaml file(add any supportable config parameter).
        4. Trigger the satellite-installer command with no option.

    :expectedresults:
        1. Tuning parameter set successfully for medium size.
        2. custom-hiera.yaml related changes should be successfully applied.

    :CaseAutomation: NotAutomated
    """


@pytest.mark.tier3
def test_installer_cap_pub_directory_accessibility(capsule_configured):
    """Verify the public directory accessibility from capsule url after disabling it from the
    custom-hiera

    :id: b5ca742b-24be-47b3-9bd9-bc5f079409ca

    :steps:
        1. Prepare the satellite and capsule and integrate them.
        2. Check the public directory accessibility from http and https capsule url
        3. Add the 'foreman_proxy_content::pub_dir::pub_dir_options:"+FollowSymLinks -Indexes"'
            in custom-hiera.yaml file on capsule.
        4. Run the satellite-installer on capsule.
        5. Check the public directory accessibility from http and https capsule url.

    :expectedresults: Public directory accessibility from http and https capsule url
        1. It should be accessible if accessibility is enabled(by default it is enabled).
        2. It should not be accessible if accessibility is disabled in custom_hiera.yaml file.

    :CaseImportance: High

    :BZ: 1860519

    :customerscenario: true
    """
    custom_hiera_location = '/etc/foreman-installer/custom-hiera.yaml'
    custom_hiera_settings = (
        'foreman_proxy_content::pub_dir::pub_dir_options: "+FollowSymLinks -Indexes"'
    )
    http_curl_command = f'curl -i {capsule_configured.url.replace("https", "http")}/pub/ -k'
    https_curl_command = f'curl -i {capsule_configured.url}/pub/ -k'
    for command in [http_curl_command, https_curl_command]:
        accessibility_check = capsule_configured.execute(command)
        assert (
            'HTTP/1.1 200 OK' in accessibility_check.stdout
            or 'HTTP/2 200' in accessibility_check.stdout
        )
    capsule_configured.get(
        local_path='custom-hiera-capsule.yaml',
        remote_path=f'{custom_hiera_location}',
    )
    _ = capsule_configured.execute(f'echo {custom_hiera_settings} >> {custom_hiera_location}')
    command_output = capsule_configured.execute('satellite-installer', timeout='20m')
    assert 'Success!' in command_output.stdout
    for command in [http_curl_command, https_curl_command]:
        accessibility_check = capsule_configured.execute(command)
        assert 'HTTP/1.1 200 OK' not in accessibility_check.stdout
        assert 'HTTP/2 200' not in accessibility_check.stdout
    capsule_configured.put(
        local_path='custom-hiera-capsule.yaml',
        remote_path=f'{custom_hiera_location}',
    )
    command_output = capsule_configured.execute('satellite-installer', timeout='20m')
    assert 'Success!' in command_output.stdout


def test_installer_capsule_with_enabled_ansible(module_capsule_configured_ansible):
    """Enables Ansible feature on external Capsule and checks the callback is set correctly

    :id: d60c475e-f4e7-11ee-af8a-98fa9b11ac24

    :steps:
        1. Have a Satellite with external Capsule integrated
        2. Enable Ansible feature on external Capsule
        3. Check the ansible callback plugin on external Capsule

    :expectedresults:
        Ansible callback plugin is overridden to "redhat.satellite.foreman"

    :CaseImportance: High

    :BZ: 2245081

    :customerscenario: true
    """
    ansible_env = '/etc/foreman-proxy/ansible.env'
    downstream_callback = 'redhat.satellite.foreman'
    callback_whitelist = module_capsule_configured_ansible.execute(
        f"awk -F= '/ANSIBLE_CALLBACK_WHITELIST/{{print$2}}' {ansible_env}"
    )
    assert callback_whitelist.stdout.strip('" \n') == downstream_callback
    callbacks_enabled = module_capsule_configured_ansible.execute(
        f"awk -F= '/ANSIBLE_CALLBACKS_ENABLED/{{print$2}}' {ansible_env}"
    )
    assert callbacks_enabled.stdout.strip('" \n') == downstream_callback


@pytest.mark.tier1
@pytest.mark.build_sanity
@pytest.mark.first_sanity
@pytest.mark.pit_server
def test_satellite_installation(installer_satellite):
    """Run a basic Satellite installation

    :id: 661206f3-2eec-403c-af26-3c5cadcd5766

    :steps:
        1. Get RHEL Host
        2. Configure satellite repos
        3. Enable satellite module
        4. Install satellite
        5. Run satellite-installer

    :expectedresults:
        1. Correct satellite packaged is installed
        2. satellite-installer runs successfully
        3. no unexpected errors in logs
        4. satellite-maintain health check runs successfully
        5. redis is set as default foreman cache

    :CaseImportance: Critical
    """
    common_sat_install_assertions(installer_satellite)

    # Verify foreman-redis is installed and set as default cache for rails
    assert installer_satellite.execute('rpm -q foreman-redis').status == 0
    settings_file = installer_satellite.load_remote_yaml_file(FOREMAN_SETTINGS_YML)
    assert settings_file.rails_cache_store.type == 'redis'


@pytest.mark.pit_server
@pytest.mark.parametrize('package', ['nmap-ncat'])
def test_weak_dependency(sat_non_default_install, package):
    """Check if Satellite and its (sub)components do not require certain (potentially insecure) packages. On an existing Satellite the package has to be either not installed or can be safely removed.

    :id: c7988920-2f8c-4646-bde9-8823a3ca96bb

    :steps:
        1. Use satellite with non-default setup (for 'nmap-ncat' enable foreman discovery plugin and install foreman-discovery-image)
        2. Attempt to remove the package

    :expectedresults:
        1. The package can be either not installed or can be removed without removing any Satellite or Foreman packages

    :BZ: 1964539

    :customerscenario: true
    """
    result = sat_non_default_install.execute(f'dnf remove -y {package} --setopt tsflags=test')

    # no satellite or foreman package to be removed
    assert 'satellite' not in result.stdout.lower()
    assert 'foreman' not in result.stdout.lower()
    # package not installed (nothing to remove) or safely removable
    assert (
        'No packages marked for removal.' in result.stderr
        or 'Transaction test succeeded.' in result.stdout
    )
