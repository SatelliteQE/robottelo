"""Test class for converting to RHEL from API

:Requirement: Convert2rhel

:CaseAutomation: Automated

:CaseComponent: Registration

:CaseImportance: Critical

:Team: Rocket

"""

import pytest
import requests

from robottelo.config import settings
from robottelo.constants import DEFAULT_ARCHITECTURE, DEFAULT_SUBSCRIPTION_NAME, REPOS


def create_repo(sat, org, repo_url, ssl_cert=None):
    """Create and sync repository"""
    product = sat.api.Product(organization=org).create()
    options = {
        'organization': org,
        'product': product,
        'content_type': 'yum',
        'url': repo_url,
        'ssl_ca_cert': ssl_cert,
        'unprotected': True,
        'verify_ssl_on_sync': False,
    }
    repo = sat.api.Repository(**options).create()
    repo.product = product
    repo.sync()
    return repo


def create_activation_key(sat, org, lce, cv, subscription_id):
    """Create activation key with subscription"""
    act_key = sat.api.ActivationKey(
        organization=org,
        content_view=cv,
        environment=lce,
    ).create()
    act_key.add_subscriptions(data={'subscription_id': subscription_id})
    content = sat.cli.ActivationKey.product_content({'id': act_key.id, 'organization-id': org.id})
    act_key.content_override(
        data={'content_overrides': [{'content_label': content[0]['label'], 'value': '1'}]}
    )
    ak_subscriptions = act_key.product_content()['results']
    ak_subscriptions[0]['enabled'] = True
    return act_key


def update_cv(sat, cv, lce, repos):
    """Update and publish Content view with repos"""
    cv = sat.api.ContentView(id=cv.id, repository=repos).update(['repository'])
    cv.publish()
    cv = cv.read()
    cv.version.sort(key=lambda version: version.id)
    cv.version[-1].promote(data={'environment_ids': lce.id, 'force': False})
    return cv


@pytest.fixture(scope='module')
def ssl_cert(module_target_sat, module_entitlement_manifest_org):
    """Create credetial with SSL cert for Oracle Linux"""
    res = requests.get(settings.repos.convert2rhel.ssl_cert_oracle)
    res.raise_for_status()
    return module_target_sat.api.ContentCredential(
        content=res.text, organization=module_entitlement_manifest_org, content_type='cert'
    ).create()


@pytest.fixture
def activation_key_rhel(
    module_target_sat, module_entitlement_manifest_org, module_lce, module_promoted_cv, version
):
    """Create activation key that will be used after conversion for registration"""
    subs = module_target_sat.api.Subscription(
        organization=module_entitlement_manifest_org.id
    ).search(query={'search': f'{DEFAULT_SUBSCRIPTION_NAME}'})
    assert subs
    return create_activation_key(
        module_target_sat,
        module_entitlement_manifest_org,
        module_lce,
        module_promoted_cv,
        subs[0].id,
    )


@pytest.fixture(scope='module')
def enable_rhel_subscriptions(module_target_sat, module_entitlement_manifest_org, version):
    """Enable and sync RHEL rpms repos"""
    major = version.split('.')[0]
    minor = ""
    if major == '8':
        repo_names = ['rhel8_bos', 'rhel8_aps']
        minor = version[1:]
    else:
        repo_names = ['rhel7']

    rh_repos = []
    tasks = []
    for name in repo_names:
        rh_repo_id = module_target_sat.api_factory.enable_rhrepo_and_fetchid(
            basearch=DEFAULT_ARCHITECTURE,
            org_id=module_entitlement_manifest_org.id,
            product=REPOS[name]['product'],
            repo=REPOS[name]['name'] + minor,
            reposet=REPOS[name]['reposet'],
            releasever=REPOS[name]['releasever'] + minor,
        )
        # Sync step because repo is not synced by default
        rh_repo = module_target_sat.api.Repository(id=rh_repo_id).read()
        task = rh_repo.sync(synchronous=False)
        tasks.append(task)
        rh_repos.append(rh_repo)
    for task in tasks:
        module_target_sat.wait_for_tasks(
            search_query=(f'id = {task["id"]}'),
            poll_timeout=2500,
            search_rate=20,
            max_tries=10,
        )
        task_status = module_target_sat.api.ForemanTask(id=task['id']).poll()
        assert task_status['result'] == 'success'
    return rh_repos


@pytest.fixture
def centos(
    module_target_sat,
    centos_host,
    module_entitlement_manifest_org,
    smart_proxy_location,
    module_promoted_cv,
    module_lce,
    version,
    enable_rhel_subscriptions,
):
    """Deploy and register Centos host"""
    major = version.split('.')[0]
    assert centos_host.execute('yum -y update').status == 0
    repo_url = settings.repos.convert2rhel.convert_to_rhel_repo.format(major)
    repo = create_repo(module_target_sat, module_entitlement_manifest_org, repo_url)
    cv = update_cv(
        module_target_sat, module_promoted_cv, module_lce, enable_rhel_subscriptions + [repo]
    )
    c2r_sub = module_target_sat.api.Subscription(
        organization=module_entitlement_manifest_org.id, name=repo.product.name
    ).search()[0]
    act_key = create_activation_key(
        module_target_sat, module_entitlement_manifest_org, module_lce, cv, c2r_sub.id
    )

    # Register CentOS host with Satellite
    command = module_target_sat.api.RegistrationCommand(
        organization=module_entitlement_manifest_org,
        activation_keys=[act_key.name],
        location=smart_proxy_location,
        insecure=True,
    ).create()
    assert centos_host.execute(command).status == 0

    if centos_host.execute('needs-restarting -r').status == 1:
        centos_host.power_control(state='reboot')

    yield centos_host
    # close ssh session before teardown, because of reboot in conversion it may cause problems
    centos_host.close()


@pytest.fixture
def oracle(
    module_target_sat,
    oracle_host,
    module_entitlement_manifest_org,
    smart_proxy_location,
    module_promoted_cv,
    module_lce,
    ssl_cert,
    version,
    enable_rhel_subscriptions,
):
    """Deploy and register Oracle host"""
    major = version.split('.')[0]
    assert oracle_host.execute('yum -y update').status == 0
    # disable rhn-client-tools because it obsoletes the subscription manager package
    oracle_host.execute('echo "exclude=rhn-client-tools" >> /etc/yum.conf')

    # Install and set correct RHEL compatible kernel and using non-UEK kernel, based on C2R docs
    result = oracle_host.execute(
        'yum install -y kernel && '
        'grubby --set-default /boot/vmlinuz-'
        '`rpm -q --qf "%{BUILDTIME}\t%{EVR}.%{ARCH}\n" kernel | sort -nr | head -1 | cut -f2`'
    )
    assert result.status == 0

    if major == '8':
        # needs-restarting missing in OEL8
        assert oracle_host.execute('dnf install -y yum-utils').status == 0
        # Fix inhibitor CHECK_FIREWALLD_AVAILABILITY::FIREWALLD_MODULES_CLEANUP_ON_EXIT_CONFIG -
        # Firewalld is set to cleanup modules after exit
        result = oracle_host.execute(
            'sed -i -- "s/CleanupModulesOnExit=yes/CleanupModulesOnExit=no/g" '
            '/etc/firewalld/firewalld.conf && firewall-cmd --reload'
        )
        assert result.status == 0

    if oracle_host.execute('needs-restarting -r').status == 1:
        oracle_host.power_control(state='reboot')

    repo_url = settings.repos.convert2rhel.convert_to_rhel_repo.format(major)
    repo = create_repo(module_target_sat, module_entitlement_manifest_org, repo_url, ssl_cert)
    cv = update_cv(
        module_target_sat, module_promoted_cv, module_lce, enable_rhel_subscriptions + [repo]
    )
    c2r_sub = module_target_sat.api.Subscription(
        organization=module_entitlement_manifest_org, name=repo.product.name
    ).search()[0]
    act_key = create_activation_key(
        module_target_sat, module_entitlement_manifest_org, module_lce, cv, c2r_sub.id
    )
    # UBI repo required for subscription-manager packages on Oracle
    ubi_url = settings.repos.convert2rhel.ubi7 if major == '7' else settings.repos.convert2rhel.ubi8

    # Register Oracle host with Satellite
    command = module_target_sat.api.RegistrationCommand(
        organization=module_entitlement_manifest_org,
        activation_keys=[act_key.name],
        location=smart_proxy_location,
        insecure=True,
        repo=ubi_url,
    ).create()
    assert oracle_host.execute(command).status == 0

    yield oracle_host
    # close ssh session before teardown, because of reboot in conversion it may cause problems
    oracle_host.close()


@pytest.fixture(scope='module')
def version(request):
    """Version of converted OS"""
    return settings.content_host.get(request.param).vm.deploy_rhel_version


@pytest.mark.e2e
@pytest.mark.parametrize('version', ['oracle7', 'oracle8'], indirect=True)
def test_convert2rhel_oracle(module_target_sat, oracle, activation_key_rhel, version):
    """Convert Oracle linux to RHEL

    :id: 7fd393f0-551a-4de0-acdd-7f026b485f79

    :steps:
        0. Have host registered to Satellite
        1. Check for operating system
        2. Convert host to RHEL

    :expectedresults: Host is converted to RHEL with correct os facts
        and subscription status

    :parametrized: yes
    """
    major = version.split('.')[0]
    assert oracle.execute('yum -y update').status == 0
    if major == '8':
        # Fix inhibitor TAINTED_KMODS::TAINTED_KMODS_DETECTED - Tainted kernel modules detected
        blacklist_cfg = '/etc/modprobe.d/blacklist.conf'
        assert oracle.execute('modprobe -r nvme_tcp').status == 0
        assert oracle.execute(f'echo "blacklist nvme_tcp" >> {blacklist_cfg}').status == 0
        assert oracle.execute(f'echo "install nvme_tcp /bin/false" >> {blacklist_cfg}').status == 0

    host_content = module_target_sat.api.Host(id=oracle.hostname).read_json()
    assert host_content['operatingsystem_name'] == f"OracleLinux {version}"

    # execute job 'Convert 2 RHEL' on host
    template_id = (
        module_target_sat.api.JobTemplate().search(query={'search': 'name="Convert to RHEL"'})[0].id
    )
    job = module_target_sat.api.JobInvocation().run(
        synchronous=False,
        data={
            'job_template_id': template_id,
            'inputs': {
                'Activation Key': activation_key_rhel.id,
                'Restart': 'yes',
                'Data telemetry': 'yes',
            },
            'targeting_type': 'static_query',
            'search_query': f'name = {oracle.hostname}',
        },
    )
    # wait for job to complete
    module_target_sat.wait_for_tasks(
        f'resource_type = JobInvocation and resource_id = {job["id"]}', poll_timeout=2500
    )
    result = module_target_sat.api.JobInvocation(id=job['id']).read()
    assert result.succeeded == 1

    # check facts: correct os and valid subscription status
    host_content = module_target_sat.api.Host(id=oracle.hostname).read_json()
    # workaround for BZ 2080347
    assert (
        host_content['operatingsystem_name'].startswith(f'RHEL Server {version}')
        or host_content['operatingsystem_name'].startswith(f'RedHat {version}')
        or host_content['operatingsystem_name'].startswith(f'RHEL {version}')
    )
    assert host_content['subscription_status'] == 0


@pytest.mark.e2e
@pytest.mark.parametrize('version', ['centos7', 'centos8'], indirect=True)
def test_convert2rhel_centos(module_target_sat, centos, activation_key_rhel, version):
    """Convert CentOS linux to RHEL

    :id: 6f698440-7d85-4deb-8dd9-363ea9003b92

    :steps:
        0. Have host registered to Satellite
        1. Check for operating system
        2. Convert host to RHEL

    :expectedresults: Host is converted to RHEL with correct os facts
        and subscription status

    :parametrized: yes
    """
    host_content = module_target_sat.api.Host(id=centos.hostname).read_json()
    major = version.split('.')[0]
    assert host_content['operatingsystem_name'] == f'CentOS {major}'
    # execute job 'Convert 2 RHEL' on host
    template_id = (
        module_target_sat.api.JobTemplate().search(query={'search': 'name="Convert to RHEL"'})[0].id
    )
    job = module_target_sat.api.JobInvocation().run(
        synchronous=False,
        data={
            'job_template_id': template_id,
            'inputs': {
                'Activation Key': activation_key_rhel.id,
                'Restart': 'yes',
                'Data telemetry': 'yes',
            },
            'targeting_type': 'static_query',
            'search_query': f'name = {centos.hostname}',
        },
    )
    # wait for job to complete
    module_target_sat.wait_for_tasks(
        f'resource_type = JobInvocation and resource_id = {job["id"]}',
        poll_timeout=2500,
        search_rate=20,
    )
    result = module_target_sat.api.JobInvocation(id=job['id']).read()
    assert result.succeeded == 1

    # check facts: correct os and valid subscription status
    host_content = module_target_sat.api.Host(id=centos.hostname).read_json()
    # workaround for BZ 2080347
    assert (
        host_content['operatingsystem_name'].startswith(f'RHEL Server {version}')
        or host_content['operatingsystem_name'].startswith(f'RedHat {version}')
        or host_content['operatingsystem_name'].startswith(f'RHEL {version}')
    )
    assert host_content['subscription_status'] == 0
