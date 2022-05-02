"""Test class for converting to RHEL from API

:Requirement: Convert2rhel

:CaseAutomation: Automated

:CaseLevel: Integration

:CaseComponent: Convert2rhel

:Assignee: shwsingh

:TestType: Functional

:Upstream: No
"""
import pytest
import requests
from nailgun import entities

from robottelo import manifests
from robottelo import ssh
from robottelo.api.utils import enable_rhrepo_and_fetchid
from robottelo.api.utils import promote
from robottelo.api.utils import upload_manifest
from robottelo.api.utils import wait_for_tasks
from robottelo.config import settings
from robottelo.constants import DEFAULT_ARCHITECTURE
from robottelo.constants import DEFAULT_SUBSCRIPTION_NAME
from robottelo.constants import REPOS


def create_repo(org, repo_url, ssl_cert=None):
    """Create and sync repository"""
    product = entities.Product(organization=org).create()
    options = {
        'organization': org,
        'product': product,
        'content_type': 'yum',
        'url': repo_url,
        'ssl_ca_cert': ssl_cert,
        'unprotected': True,
        'verify_ssl_on_sync': False,
    }
    repo = entities.Repository(**options).create()
    repo.product = product
    repo.sync()
    return repo


def create_activation_key(org, lce, cv, subscription_id):
    """Create activation key with subscription"""
    act_key = entities.ActivationKey(
        organization=org,
        content_view=cv,
        environment=lce,
    ).create()
    act_key.add_subscriptions(data={'subscription_id': subscription_id})
    return act_key


def update_cv(cv, lce, repos):
    """Update and publish Content view with repos"""
    cv = entities.ContentView(id=cv.id, repository=repos).update(["repository"])
    cv.publish()
    cv = cv.read()
    promote(cv.version[-1], environment_id=lce.id)
    return cv


def register_host(act_key, module_org, module_loc, hostname, ubi=None):
    """Register host to satellite"""
    # generate registration command
    command = entities.RegistrationCommand(
        organization=module_org,
        activation_keys=[act_key.name],
        location=module_loc,
        insecure=True,
        repo=ubi,
    ).create()['registration_command']
    result = ssh.command(command, hostname=hostname)
    assert result.status == 0


@pytest.fixture(scope="module")
def ssl_cert(module_org):
    """Create credetial with SSL cert for Oracle Linux"""
    res = requests.get(settings.repos.convert2rhel.ssl_cert_oracle)
    res.raise_for_status()
    return entities.ContentCredential(
        content=res.text, organization=module_org, content_type='cert'
    ).create()


@pytest.fixture(scope='module')
def manifest(module_org):
    with manifests.clone() as manifest:
        upload_manifest(module_org.id, manifest.content)


@pytest.fixture
def activation_key_rhel(module_org, module_lce, module_promoted_cv, version):
    """Create activation key that will be used after conversion for registration"""
    subs = entities.Subscription(organization=module_org).search(
        query={'search': f'{DEFAULT_SUBSCRIPTION_NAME}'}
    )
    assert subs
    return create_activation_key(module_org, module_lce, module_promoted_cv, subs[0].id)


@pytest.fixture(scope='module')
def enable_rhel_subscriptions(module_org, manifest, version):
    """Enable and sync RHEL rpms repos"""
    major = version.split('.')[0]
    minor = ""
    if major == '8':
        repo_names = ['rhel8_bos', 'rhel8_aps']
        minor = version[1:]
    else:
        repo_names = ['rhel7']

    rh_repos = []
    for name in repo_names:
        rh_repo_id = enable_rhrepo_and_fetchid(
            basearch=DEFAULT_ARCHITECTURE,
            org_id=module_org.id,
            product=REPOS[name]['product'],
            repo=REPOS[name]['name'] + minor,
            reposet=REPOS[name]['reposet'],
            releasever=REPOS[name]['releasever'] + minor,
        )
        # Sync step because repo is not synced by default
        rh_repo = entities.Repository(id=rh_repo_id).read()
        rh_repo.sync(timeout=2500)
        rh_repos.append(rh_repo)
    return rh_repos


@pytest.fixture
def centos(
    centos_host,
    module_org,
    smart_proxy_location,
    module_promoted_cv,
    module_lce,
    version,
    enable_rhel_subscriptions,
):
    """Deploy and register Centos host"""
    # updating centos packages on CentOS 8 is necessary for conversion
    major = version.split('.')[0]
    if major == '8':
        centos_host.execute("yum update -y centos-*")
    repo = create_repo(module_org, settings.repos.convert2rhel.convert_to_rhel_repo.format(major))
    cv = update_cv(module_promoted_cv, module_lce, enable_rhel_subscriptions + [repo])
    c2r_sub = entities.Subscription(organization=module_org, name=repo.product.name).search()[0]
    act_key = create_activation_key(module_org, module_lce, cv, c2r_sub.id)
    register_host(act_key, module_org, smart_proxy_location, centos_host.hostname)
    yield centos_host
    # close ssh session before teardown, because of reboot in conversion it may cause problems
    centos_host.close()


@pytest.fixture
def oracle(
    oracle_host,
    module_org,
    smart_proxy_location,
    module_promoted_cv,
    module_lce,
    ssl_cert,
    version,
    enable_rhel_subscriptions,
):
    """Deploy and register Oracle host"""
    # disable rhn-client-tools because it obsoletes the subscription manager package
    oracle_host.execute('echo "exclude=rhn-client-tools" >> /etc/yum.conf')
    # install and set correct kernel, based on convert2rhel docs
    result = oracle_host.execute(
        'yum install -y kernel && '
        'grubby --set-default /boot/vmlinuz-'
        '`rpm -q --qf "%{BUILDTIME}\t%{EVR}.%{ARCH}\n" kernel | sort -nr | head -1 | cut -f2`'
    )
    assert result.status == 0
    oracle_host.power_control(state='reboot')
    major = version.split('.')[0]
    repo = create_repo(
        module_org, settings.repos.convert2rhel.convert_to_rhel_repo.format(major), ssl_cert
    )
    cv = update_cv(module_promoted_cv, module_lce, enable_rhel_subscriptions + [repo])
    c2r_sub = entities.Subscription(organization=module_org, name=repo.product.name).search()[0]
    act_key = create_activation_key(module_org, module_lce, cv, c2r_sub.id)
    ubi_url = settings.repos.convert2rhel.ubi7 if major == '7' else settings.repos.convert2rhel.ubi8
    ubi = create_repo(module_org, ubi_url)
    ubi_repo = ubi.full_path.replace('https', 'http')
    register_host(act_key, module_org, smart_proxy_location, oracle_host.hostname, ubi_repo)
    yield oracle_host
    # close ssh session before teardown, because of reboot in conversion it may cause problems
    oracle_host.close()


@pytest.fixture(scope='module')
def version(request):
    """Version of converted OS"""
    return settings.content_host.deploy_kwargs.get(request.param).release


@pytest.mark.parametrize(
    "version",
    ['oracle7', 'oracle8'],
    indirect=True,
)
def test_convert2rhel_oracle(oracle, activation_key_rhel, version):
    """Convert Oracle linux to RHEL

    :id: 7fd393f0-551a-4de0-acdd-7f026b485f79

    :Steps:
        0. Have host registered to Satellite
        1. Check for operating system
        2. Convert host to RHEL

    :expectedresults: Host is converted to RHEL with correct os facts
        and subscription status

    :parametrized: yes

    :CaseImportance: Medium
    """
    host_content = entities.Host(id=oracle.hostname).read_json()
    assert host_content['operatingsystem_name'] == f"OracleLinux {version}"

    # execute job 'Convert 2 RHEL' on host
    template_id = entities.JobTemplate().search(query={'search': 'name="Convert to RHEL"'})[0].id
    job = entities.JobInvocation().run(
        synchronous=False,
        data={
            'job_template_id': template_id,
            'inputs': {
                'Activation Key': activation_key_rhel.id,
                'Restart': 'yes',
            },
            'targeting_type': 'static_query',
            'search_query': f'name = {oracle.hostname}',
        },
    )
    # wait for job to complete
    wait_for_tasks(
        f'resource_type = JobInvocation and resource_id = {job["id"]}', poll_timeout=1000
    )
    result = entities.JobInvocation(id=job['id']).read()
    assert result.succeeded == 1

    # check facts: correct os and valid subscription status
    host_content = entities.Host(id=oracle.hostname).read_json()
    assert (
        host_content['operatingsystem_name'].startswith(f"RHEL Server {version}")
        or host_content['operatingsystem_name'].startswith(f"RedHat {version}")
        or host_content['operatingsystem_name'].startswith(f"RHEL {version}")
    )
    assert host_content['subscription_status'] == 0


@pytest.mark.parametrize("version", ['centos7', 'centos8'], indirect=True)
def test_convert2rhel_centos(centos, activation_key_rhel, version):
    """Convert Centos linux to RHEL

    :id: 6f698440-7d85-4deb-8dd9-363ea9003b92

    :Steps:
        0. Have host registered to Satellite
        1. Check for operating system
        2. Convert host to RHEL

    :expectedresults: Host is converted to RHEL with correct os facts
        and subscription status

    :parametrized: yes

    :CaseImportance: Medium
    """
    host_content = entities.Host(id=centos.hostname).read_json()
    major = version.split('.')[0]
    assert host_content['operatingsystem_name'] == f"CentOS {major}"

    # execute job 'Convert 2 RHEL' on host
    template_id = entities.JobTemplate().search(query={'search': 'name="Convert to RHEL"'})[0].id
    job = entities.JobInvocation().run(
        synchronous=False,
        data={
            'job_template_id': template_id,
            'inputs': {
                'Activation Key': activation_key_rhel.id,
                'Restart': 'yes',
            },
            'targeting_type': 'static_query',
            'search_query': f'name = {centos.hostname}',
        },
    )
    # wait for job to complete
    wait_for_tasks(
        f'resource_type = JobInvocation and resource_id = {job["id"]}', poll_timeout=1000
    )
    result = entities.JobInvocation(id=job['id']).read()
    assert result.succeeded == 1

    # check facts: correct os and valid subscription status
    host_content = entities.Host(id=centos.hostname).read_json()
    assert (
        host_content['operatingsystem_name'].startswith(f"RHEL Server {version}")
        or host_content['operatingsystem_name'].startswith(f"RedHat {version}")
        or host_content['operatingsystem_name'].startswith(f"RHEL {version}")
    )
    assert host_content['subscription_status'] == 0
