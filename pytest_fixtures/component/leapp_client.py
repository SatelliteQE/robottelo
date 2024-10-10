from broker import Broker
import pytest

from robottelo.config import settings
from robottelo.constants import PRDS
from robottelo.hosts import ContentHost
from robottelo.logging import logger

synced_repos = pytest.StashKey[dict]

RHEL7_VER = '7.9'
RHEL8_VER = '8.10'
RHEL9_VER = '9.4'

RHEL_REPOS = {
    'rhel7_server': {
        'id': 'rhel-7-server-rpms',
        'name': f'Red Hat Enterprise Linux 7 Server RPMs x86_64 {RHEL7_VER}',
        'releasever': RHEL7_VER,
        'reposet': 'Red Hat Enterprise Linux 7 Server (RPMs)',
        'product': 'Red Hat Enterprise Linux Server',
    },
    'rhel7_server_extras': {
        'id': 'rhel-7-server-extras-rpms',
        'name': 'Red Hat Enterprise Linux 7 Server - Extras RPMs x86_64',
        'releasever': '7',
        'reposet': 'Red Hat Enterprise Linux 7 Server - Extras (RPMs)',
        'product': 'Red Hat Enterprise Linux Server',
    },
    'rhel8_bos': {
        'id': 'rhel-8-for-x86_64-baseos-rpms',
        'name': f'Red Hat Enterprise Linux 8 for x86_64 - BaseOS RPMs {RHEL8_VER}',
        'releasever': RHEL8_VER,
        'reposet': 'Red Hat Enterprise Linux 8 for x86_64 - BaseOS (RPMs)',
    },
    'rhel8_aps': {
        'id': 'rhel-8-for-x86_64-appstream-rpms',
        'name': f'Red Hat Enterprise Linux 8 for x86_64 - AppStream RPMs {RHEL8_VER}',
        'releasever': RHEL8_VER,
        'reposet': 'Red Hat Enterprise Linux 8 for x86_64 - AppStream (RPMs)',
    },
    'rhel9_bos': {
        'id': 'rhel-9-for-x86_64-baseos-rpms',
        'name': f'Red Hat Enterprise Linux 9 for x86_64 - BaseOS RPMs {RHEL9_VER}',
        'releasever': RHEL9_VER,
        'reposet': 'Red Hat Enterprise Linux 9 for x86_64 - BaseOS (RPMs)',
    },
    'rhel9_aps': {
        'id': 'rhel-9-for-x86_64-appstream-rpms',
        'name': f'Red Hat Enterprise Linux 9 for x86_64 - AppStream RPMs {RHEL9_VER}',
        'releasever': RHEL9_VER,
        'reposet': 'Red Hat Enterprise Linux 9 for x86_64 - AppStream (RPMs)',
    },
}


@pytest.fixture(scope='module')
def module_stash(request):
    """Module scoped stash for storing data between tests"""
    # Please refer the documentation for more details on stash
    # https://docs.pytest.org/en/latest/reference/reference.html#stash
    request.node.stash[synced_repos] = {}
    return request.node.stash


@pytest.fixture(scope='module')
def module_leapp_lce(module_target_sat, module_sca_manifest_org):
    return module_target_sat.api.LifecycleEnvironment(organization=module_sca_manifest_org).create()


@pytest.fixture
def function_leapp_cv(module_target_sat, module_sca_manifest_org, leapp_repos, module_leapp_lce):
    function_leapp_cv = module_target_sat.api.ContentView(
        organization=module_sca_manifest_org
    ).create()
    function_leapp_cv.repository = leapp_repos
    function_leapp_cv = function_leapp_cv.update(['repository'])
    function_leapp_cv.publish()
    cvv = function_leapp_cv.read().version[0]
    cvv.promote(data={'environment_ids': module_leapp_lce.id, 'force': True})
    return function_leapp_cv.read()


@pytest.fixture
def function_leapp_ak(
    module_target_sat,
    function_leapp_cv,
    module_leapp_lce,
    module_sca_manifest_org,
):
    return module_target_sat.api.ActivationKey(
        content_view=function_leapp_cv,
        environment=module_leapp_lce,
        organization=module_sca_manifest_org,
    ).create()


@pytest.fixture
def leapp_repos(
    default_architecture,
    module_stash,
    upgrade_path,
    module_target_sat,
    module_sca_manifest_org,
):
    """Enable and sync RHEL BaseOS, AppStream repositories"""
    source = upgrade_path['source_version']
    target = upgrade_path['target_version']
    all_repos = []
    for rh_repo_key in RHEL_REPOS:
        release_version = RHEL_REPOS[rh_repo_key]['releasever']
        if release_version in str(source) or release_version in target:
            prod = 'rhel' if 'rhel7' in rh_repo_key else rh_repo_key.split('_')[0]
            repo_id = module_target_sat.api_factory.enable_rhrepo_and_fetchid(
                basearch=default_architecture.name,
                org_id=module_sca_manifest_org.id,
                product=PRDS[prod],
                repo=RHEL_REPOS[rh_repo_key]['name'],
                reposet=RHEL_REPOS[rh_repo_key]['reposet'],
                releasever=release_version,
            )
            rh_repo = module_target_sat.api.Repository(id=repo_id).read()
            all_repos.append(rh_repo)
            if module_stash[synced_repos].get(rh_repo_key, None):
                logger.info('Repo %s already synced, not syncing it', rh_repo_key)
            else:
                module_stash[synced_repos][rh_repo_key] = True
                rh_repo.sync(timeout=1800)
    return all_repos


@pytest.fixture
def verify_target_repo_on_satellite(
    module_target_sat,
    function_leapp_cv,
    module_sca_manifest_org,
    module_leapp_lce,
    upgrade_path,
    leapp_repos,
):
    """Verify target rhel version repositories have been added in correct CV, LCE on Satellite"""
    target_rhel_major_ver = upgrade_path['target_version'].split('.')[0]
    cmd_out = module_target_sat.cli.Repository.list(
        {
            'search': f'content_label ~ rhel-{target_rhel_major_ver}',
            'content-view-id': function_leapp_cv.id,
            'organization-id': module_sca_manifest_org.id,
            'lifecycle-environment-id': module_leapp_lce.id,
        }
    )
    repo_names = [out['name'] for out in cmd_out]
    if target_rhel_major_ver == '9':
        assert RHEL_REPOS['rhel9_bos']['name'] in repo_names
        assert RHEL_REPOS['rhel9_aps']['name'] in repo_names
    else:
        assert RHEL_REPOS['rhel8_bos']['name'] in repo_names
        assert RHEL_REPOS['rhel8_aps']['name'] in repo_names


@pytest.fixture
def custom_leapp_host(upgrade_path, module_target_sat, module_sca_manifest_org, function_leapp_ak):
    """Checkout content host and register with satellite"""
    deploy_args = {}
    deploy_args['deploy_rhel_version'] = upgrade_path['source_version']
    with Broker(
        workflow='deploy-rhel',
        host_class=ContentHost,
        deploy_rhel_version=upgrade_path['source_version'],
        deploy_flavor=settings.flavors.default,
        deploy_network_type='ipv6' if settings.server.is_ipv6 else 'ipv4',
    ) as chost:
        result = chost.register(
            module_sca_manifest_org, None, function_leapp_ak.name, module_target_sat
        )
        assert result.status == 0, f'Failed to register host: {result.stderr}'
        yield chost


@pytest.fixture
def precondition_check_upgrade_and_install_leapp_tool(custom_leapp_host):
    """Clean-up directory if in-place upgrade already performed,
    set rhel release version, update system and install leapp-upgrade and fix known inhibitors before upgrade"""
    source_rhel = custom_leapp_host.os_version.base_version
    custom_leapp_host.run('rm -rf /root/tmp_leapp_py3')
    custom_leapp_host.run('yum repolist')
    custom_leapp_host.run(f'subscription-manager release --set {source_rhel}')
    assert custom_leapp_host.run('yum update -y').status == 0
    assert custom_leapp_host.run('yum install leapp-upgrade -y').status == 0
    if custom_leapp_host.run('needs-restarting -r').status == 1:
        custom_leapp_host.power_control(state='reboot', ensure=True)

    # Fixing known inhibitors for source rhel version 8
    if custom_leapp_host.os_version.major == 8:
        # Inhibitor - Firewalld Configuration AllowZoneDrifting Is Unsupported
        assert (
            custom_leapp_host.run(
                'sed -i "s/^AllowZoneDrifting=.*/AllowZoneDrifting=no/" /etc/firewalld/firewalld.conf'
            ).status
            == 0
        )
        assert (
            custom_leapp_host.run(
                'echo -e "\nPermitRootLogin yes" >> /etc/ssh/sshd_config; systemctl restart sshd'
            ).status
            == 0
        )
