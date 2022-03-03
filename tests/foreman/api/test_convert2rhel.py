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
from broker import VMBroker
from nailgun import entities

from robottelo import manifests
from robottelo import ssh
from robottelo.api.utils import enable_rhrepo_and_fetchid
from robottelo.api.utils import promote
from robottelo.api.utils import upload_manifest
from robottelo.api.utils import wait_for_tasks
from robottelo.constants import CONVERT_TO_RHEL_REPO
from robottelo.constants import DEFAULT_ARCHITECTURE
from robottelo.constants import DEFAULT_SUBSCRIPTION_NAME
from robottelo.constants import REPOS
from robottelo.constants import SSL_CERT_ORACLE
from robottelo.constants import UBI_ORACLE7
from robottelo.constants import UBI_ORACLE8
from robottelo.hosts import ContentHost


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
    res = requests.get(SSL_CERT_ORACLE)
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


def enable_rhel_repos(org, repos):
    rh_repos = []
    for repo in repos:
        rh_repo_id = enable_rhrepo_and_fetchid(
            basearch=DEFAULT_ARCHITECTURE,
            org_id=org.id,
            product=REPOS[repo]['product'],
            repo=REPOS[repo]['name'],
            reposet=REPOS[repo]['reposet'],
            releasever=REPOS[repo]['releasever'],
        )
        # Sync step because repo is not synced by default
        rh_repo = entities.Repository(id=rh_repo_id).read()
        rh_repo.sync(timeout=2500)
        rh_repos.append(rh_repo)
    return rh_repos


@pytest.fixture(scope='module')
def enable_rhel7_subscriptions(module_org, manifest):
    """Enable and sync RHEL7 server rmps repo"""
    return enable_rhel_repos(module_org, ['rhel7'])


@pytest.fixture(scope='module')
def enable_rhel8_subscriptions(module_org, manifest):
    """Enable and sync RHEL8 baseos and appstream repos"""
    return enable_rhel_repos(module_org, ['rhel8_bos', 'rhel8_aps'])


@pytest.fixture
def centos_host(
    request, default_sat, module_org, smart_proxy_location, module_promoted_cv, module_lce, version
):
    """Deploy and register Centos host"""
    rh_repos = request.getfixturevalue(f"enable_rhel{version}_subscriptions")
    conf = {
        "workflow": "deploy-centos",
        "deploy_scenario": "centos",
        "deploy_rhel_version": version,
    }
    with VMBroker(**conf, host_classes={'host': ContentHost}) as host:
        host.install_katello_ca(default_sat)
        # updating centos packages on CentOS 8 is necessary for conversion
        if version == '8':
            host.execute("yum update -y centos-*")
        repo = create_repo(module_org, CONVERT_TO_RHEL_REPO.format(version))
        cv = update_cv(module_promoted_cv, module_lce, rh_repos + [repo])
        c2r_sub = entities.Subscription(organization=module_org, name=repo.product.name).search()[0]
        act_key = create_activation_key(module_org, module_lce, cv, c2r_sub.id)
        register_host(act_key, module_org, smart_proxy_location, host.hostname)
        yield host
        # close ssh session before teardown, because of reboot in conversion it may cause problems
        host.close()


@pytest.fixture
def oracle_host(
    request,
    default_sat,
    module_org,
    smart_proxy_location,
    module_promoted_cv,
    module_lce,
    ssl_cert,
    version,
):
    """Deploy and register Oracle host"""
    rh_repos = request.getfixturevalue(f"enable_rhel{version}_subscriptions")
    conf = {
        "workflow": "deploy-oracle-linux",
        "deploy_scenario": "oracle",
        "deploy_rhel_version": version,
    }
    with VMBroker(**conf, host_classes={'host': ContentHost}) as host:
        # disable rhn-client-tools because it obsoletes the subscribtion manager package
        host.execute('echo "exclude=rhn-client-tools" >> /etc/yum.conf')
        # install and set correct kernel, based on convert2rhel docs
        result = host.execute(
            'yum install -y kernel && '
            'grubby --set-default /boot/vmlinuz-'
            '`rpm -q --qf "%{BUILDTIME}\t%{EVR}.%{ARCH}\n" kernel | sort -nr | head -1 | cut -f2`'
        )
        assert result.status == 0
        host.install_katello_ca(default_sat)
        host.power_control(state='reboot')
        repo = create_repo(module_org, CONVERT_TO_RHEL_REPO.format(version), ssl_cert)
        cv = update_cv(module_promoted_cv, module_lce, rh_repos + [repo])
        c2r_sub = entities.Subscription(organization=module_org, name=repo.product.name).search()[0]
        act_key = create_activation_key(module_org, module_lce, cv, c2r_sub.id)
        ubi_url = UBI_ORACLE7 if version == '7' else UBI_ORACLE8
        ubi = create_repo(module_org, ubi_url)
        ubi_repo = ubi.full_path.replace('https', 'http')
        register_host(act_key, module_org, smart_proxy_location, host.hostname, ubi_repo)
        yield host
        # close ssh session before teardown, because of reboot in conversion it may cause problems
        host.close()


@pytest.fixture
def version(request):
    """Major version of converted OS"""
    return request.param


@pytest.mark.parametrize(
    "version",
    ['7', '8'],
    indirect=True,
)
def test_convert2rhel_oracle(oracle_host, activation_key_rhel, version):
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
    host_content = entities.Host(id=oracle_host.hostname).read_json()
    assert host_content['operatingsystem_name'].startswith(f"OracleLinux {version}")

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
            'search_query': f'name = {oracle_host.hostname}',
        },
    )
    # wait for job to complete
    wait_for_tasks(
        f'resource_type = JobInvocation and resource_id = {job["id"]}', poll_timeout=1000
    )
    result = entities.JobInvocation(id=job['id']).read()
    assert result.succeeded == 1

    # check facts: correct os and valid subscription status
    host_content = entities.Host(id=oracle_host.hostname).read_json()
    os_name = 'RHEL Server' if version == '7' else 'RedHat'
    assert host_content['operatingsystem_name'].startswith(f"{os_name} {version}")
    assert host_content['subscription_status'] == 0


@pytest.mark.parametrize("version", ['7', '8'], indirect=True)
def test_convert2rhel_centos(centos_host, activation_key_rhel, version):
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
    host_content = entities.Host(id=centos_host.hostname).read_json()
    assert host_content['operatingsystem_name'].startswith(f"CentOS {version}")

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
            'search_query': f'name = {centos_host.hostname}',
        },
    )
    # wait for job to complete
    wait_for_tasks(
        f'resource_type = JobInvocation and resource_id = {job["id"]}', poll_timeout=1000
    )
    result = entities.JobInvocation(id=job['id']).read()
    assert result.succeeded == 1

    # check facts: correct os and valid subscription status
    host_content = entities.Host(id=centos_host.hostname).read_json()
    os_name = 'RHEL Server' if version == '7' else 'RedHat'
    assert host_content['operatingsystem_name'].startswith(f"{os_name} {version}")
    assert host_content['subscription_status'] == 0
