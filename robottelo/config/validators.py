from dynaconf import Validator

from robottelo.constants import AZURERM_VALID_REGIONS
from robottelo.constants import VALID_GCE_ZONES


VALIDATORS = dict(
    server=[
        Validator('server.hostname', must_exist=False, default=''),
        Validator('server.hostnames', must_exist=True, is_type_of=list),
        Validator('server.version.release', must_exist=True),
        Validator('server.version.source', must_exist=True),
        Validator(
            'server.xdist_behavior', must_exist=True, is_in=['run-on-one', 'balance', 'on-demand']
        ),
        Validator('server.auto_checkin', default=False, is_type_of=bool),
        (
            Validator('server.ssh_key', must_exist=True)
            | Validator('server.ssh_password', must_exist=True)
            | Validator('server.ssh_key_string', must_exist=True)
        ),
        Validator('server.admin_password', default='changeme'),
        Validator('server.admin_username', default='admin'),
        Validator('server.deploy_workflow', must_exist=True),
        Validator('server.scheme', default='https'),
        Validator('server.port', default=443),
        Validator('server.ssh_username', default='root'),
        Validator('server.ssh_password', default=None),
    ],
    content_host=[
        Validator('content_host.rhel_versions', must_exist=True),
        Validator('content_host.default_rhel_version', must_exist=True),
        Validator('content_host.deploy_workflow', must_exist=True),
    ],
    subscription=[
        Validator('subscription.rhn_username', must_exist=True),
        Validator('subscription.rhn_password', must_exist=True),
        Validator('subscription.rhn_poolid', must_exist=True),
    ],
    ansible_hub=[
        Validator('ansible_hub.url', must_exist=True),
        Validator('ansible_hub.token', must_exist=True),
        Validator('ansible_hub.sso_url', must_exist=True),
    ],
    azurerm=[
        Validator(
            'azurerm.client_id',
            'azurerm.client_secret',
            'azurerm.subscription_id',
            'azurerm.tenant_id',
            'azurerm.azure_region',
            'azurerm.ssh_pub_key',
            'azurerm.username',
            'azurerm.password',
            'azurerm.azure_subnet',
            must_exist=True,
        ),
        Validator('azurerm.azure_region', is_in=AZURERM_VALID_REGIONS),
    ],
    broker=[Validator('broker.broker_directory', default='.')],
    bugzilla=[
        Validator('bugzilla.url', default='https://bugzilla.redhat.com'),
        Validator('bugzilla.api_key', must_exist=True),
    ],
    capsule=[
        Validator('capsule.instance_name', must_exist=True),
        Validator('capsule.version.release', must_exist=True),
        Validator('capsule.version.source', must_exist=True),
        Validator('capsule.deploy_workflow', must_exist=True),
    ],
    certs=[
        Validator(
            'certs.cert_file',
            'certs.key_file',
            'certs.req_file',
            'certs.ca_bundle_file',
            must_exist=True,
        )
    ],
    clients=[Validator('clients.provisioning_server')],
    libvirt=[
        Validator('libvirt.libvirt_hostname', must_exist=True),
        Validator('libvirt.libvirt_image_dir', default='/var/lib/libvirt/images'),
    ],
    container_repo=[
        Validator(
            'container_repo.registry_url',
            'container_repo.registry_username',
            'container_repo.registry_password',
            'container_repo.repos_to_sync',
            must_exist=True,
        )
    ],
    discovery=[Validator('discovery.discovery_iso', must_exist=True)],
    distro=[
        Validator(
            'distro.image_el7',
            'distro.image_el6',
            'distro.image_el8',
            'distro.image_sles11',
            'distro.image_sles12',
            must_exist=True,
        )
    ],
    docker=[
        Validator(
            'docker.external_registry_1',
            'docker.private_registry_url',
            'docker.private_registry_name',
            'docker.private_registry_username',
            'docker.private_registry_password',
            must_exist=True,
        )
    ],
    ec2=[
        Validator(
            'ec2.access_key',
            'ec2.secret_key',
            'ec2.region',
            must_exist=True,
        ),
        Validator('ec2.managed_ip', is_in=('Private', 'Public'), default='Private'),
        Validator('ec2.region', default='us-west-2'),
        Validator('ec2.security_group', default=['default']),
    ],
    fake_capsules=[Validator('fake_capsules.port_range', must_exist=True)],
    # FIXME: we don't check if 'default' is defined
    # since that's YAML, could we change API and check for presence of at least one setting?
    fake_manifest=[
        Validator(
            'fake_manifest.cert_url', 'fake_manifest.key_url', 'fake_manifest.url', must_exist=True
        ),
    ],
    gce=[
        Validator(
            'gce.cert_path',
            'gce.zone',
            'gce.cert',
            must_exist=True,
        ),
        Validator('gce.cert_path', startswith='/usr/share/foreman/'),
        Validator('gce.zone', is_in=VALID_GCE_ZONES),
    ],
    git=[
        Validator(
            'git.username',
            'git.password',
            'git.url',
            must_exist=True,
        ),
    ],
    http_proxy=[
        Validator(
            'http_proxy.un_auth_proxy_url',
            'http_proxy.auth_proxy_url',
            'http_proxy.username',
            'http_proxy.password',
            must_exist=True,
        )
    ],
    ipa=[
        Validator(
            'ipa.basedn_ipa',
            'ipa.grpbasedn_ipa',
            'ipa.hostname_ipa',
            'ipa.password_ipa',
            'ipa.username_ipa',
            'ipa.user_ipa',
            'ipa.otp_user',
            'ipa.time_based_secret',
            'ipa.disabled_ipa_user',
            'ipa.group_users',
            'ipa.groups',
            must_exist=True,
        )
    ],
    ldap=[
        Validator(
            'ldap.basedn',
            'ldap.grpbasedn',
            'ldap.hostname',
            'ldap.nameserver',
            'ldap.password',
            'ldap.realm',
            'ldap.username',
            'ldap.workgroup',
            must_exist=True,
        )
    ],
    open_ldap=[
        Validator(
            'open_ldap.base_dn',
            'open_ldap.group_base_dn',
            'open_ldap.hostname',
            'open_ldap.password',
            'open_ldap.username',
            'open_ldap.open_ldap_user',
            must_exist=True,
        )
    ],
    oscap=[
        Validator(
            'oscap.content_path',
            'oscap.tailoring_path',
            must_exist=True,
        )
    ],
    osp=[
        Validator(
            'osp.hostname',
            'osp.username',
            'osp.password',
            'osp.tenant',
            'osp.project_domain_id',
            'osp.security_group',
            'osp.vm_name',
            'osp.image_os',
            'osp.image_arch',
            'osp.image_username',
            'osp.image_name',
            must_exist=True,
        )
    ],
    performance=[Validator('performance.time_hammer', default=False)],
    report_portal=[
        Validator(
            'report_portal.portal_url',
            'report_portal.project',
            'report_portal.api_key',
            must_exist=True,
        ),
        Validator('report_portal.fail_threshold', default=20),
    ],
    repos=[
        Validator(
            'repos.rhel6_repo',
            'repos.rhel7_repo',
            'repos.rhel8_repo',
            must_exist=True,
            is_type_of=str,
        ),
        Validator(
            'repos.rhel6_os',
            'repos.rhel7_os',
            'repos.rhel8_os.baseos',
            'repos.rhel8_os.appstream',
            'repos.rhel7_optional',
            'repos.rhel7_extras',
            'repos.sattools_repo.rhel6',
            'repos.sattools_repo.rhel7',
            'repos.sattools_repo.rhel8',
            'repos.satmaintenance_repo',
            'repos.rhscl_repo',
            'repos.ansible_repo',
            'repos.swid_tools_repo',
            must_exist=False,
            is_type_of=str,
        ),
    ],
    rhev=[
        Validator(
            'rhev.hostname',
            'rhev.username',
            'rhev.password',
            'rhev.datacenter',
            'rhev.vm_name',
            'rhev.storage_domain',
            'rhev.image_os',
            'rhev.image_arch',
            'rhev.image_username',
            'rhev.image_password',
            'rhev.image_name',
            must_exist=True,
        )
    ],
    rhsso=[
        Validator(
            'rhsso.host_name',
            'rhsso.host_url',
            'rhsso.rhsso_user',
            'rhsso.user_password',
            'rhsso.realm',
            must_exist=True,
        )
    ],
    shared_function=[
        Validator('shared_function.storage', is_in=('file', 'redis'), default='file'),
        Validator('shared_function.share_timeout', lte=86400, default=86400),
        Validator('shared_function.scope', default=None),
        Validator('shared_function.enabled', default=False),
        Validator('shared_function.lock_timeout', default=7200),
        Validator('shared_function.redis_host', default='localhost'),
        Validator('shared_function.redis_port', default=6379),
        Validator('shared_function.redis_db', default=0),
        Validator('shared_function.call_retries', default=2),
        Validator('shared_function.redis_password', default=None),
    ],
    upgrade=[
        Validator('upgrade.rhev_cap_host', must_exist=False)
        | Validator('upgrade.capsule_hostname', must_exist=False),
        Validator('upgrade.rhev_capsule_ak', must_exist=False)
        | Validator('upgrade.capsule_ak', must_exist=False),
    ],
    vlan_networking=[
        Validator(
            'vlan_networking.subnet',
            'vlan_networking.netmask',
            'vlan_networking.gateway',
            must_exist=True,
        ),
        Validator('vlan_networking.dhcp_ipam', is_in=('Internal DB', 'DHCP')),
        # one, and only one, of ('bridge', 'network') must be defined
        (
            Validator('vlan_networking.bridge', must_exist=True)
            & Validator('vlan_networking.network', must_exist=False)
        )
        | (
            Validator('vlan_networking.bridge', must_exist=False)
            & Validator('vlan_networking.network', must_exist=True)
        ),
        # both dhcp_from and dhcp_to are defined, or neither is
        Validator(
            'vlan_networking.dhcp_from',
            'vlan_networking.dhcp_to',
            must_exist=True,
        )
        | Validator(
            'vlan_networking.dhcp_from',
            'vlan_networking.dhcp_to',
            must_exist=False,
        ),
    ],
    vmware=[
        Validator(
            'vmware.vcenter',
            'vmware.username',
            'vmware.password',
            'vmware.datacenter',
            'vmware.vm_name',
            'vmware.image_os',
            'vmware.image_arch',
            'vmware.image_username',
            'vmware.image_password',
            'vmware.image_name',
            must_exist=True,
        )
    ],
)
