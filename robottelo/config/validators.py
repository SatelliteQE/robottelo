from dynaconf import Validator

from robottelo.constants import AZURERM_VALID_REGIONS, VALID_GCE_ZONES

VALIDATORS = dict(
    supportability=[
        Validator('supportability.content_hosts.rhel.versions', must_exist=True, is_type_of=list),
        Validator(
            'supportability.content_hosts.default_os_name', must_exist=True, default='RedHat'
        ),
    ],
    server=[
        Validator('server.hostname', is_type_of=str),
        Validator('server.hostnames', must_exist=True, is_type_of=list),
        Validator('server.version.release', must_exist=True),
        Validator('server.version.source', default='internal', is_in=['internal', 'ga', 'nightly']),
        Validator('server.version.rhel_version', must_exist=True, cast=str),
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
        Validator('server.deploy_workflows', must_exist=True, is_type_of=dict),
        Validator('server.deploy_workflows.product', must_exist=True),
        Validator('server.deploy_workflows.os', must_exist=True),
        Validator('server.deploy_arguments', must_exist=True, is_type_of=dict, default={}),
        Validator('server.scheme', default='https'),
        Validator('server.port', default=443),
        Validator('server.ssh_username', default='root'),
        Validator('server.ssh_password', default=None),
        Validator('server.verify_ca', default=False),
        Validator('server.is_ipv6', is_type_of=bool, default=False),
        # validate http_proxy_ipv6_url only if is_ipv6 is True
        Validator(
            'server.http_proxy_ipv6_url',
            is_type_of=str,
            when=Validator('server.is_ipv6', eq=True),
        ),
    ],
    content_host=[
        Validator('content_host.default_rhel_version', must_exist=True),
    ],
    subscription=[
        Validator('subscription.rhn_username', must_exist=True),
        Validator('subscription.rhn_password', must_exist=True),
        Validator('subscription.rhn_poolid', must_exist=True),
        Validator('subscription.lifecycle_api_url', must_exist=True),
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
        Validator('capsule.version.release', must_exist=True),
        Validator(
            'capsule.version.source', default='internal', is_in=['internal', 'ga', 'nightly']
        ),
        Validator('capsule.deploy_workflows', must_exist=True, is_type_of=dict),
        Validator('capsule.deploy_workflows.product', must_exist=True),
        Validator('capsule.deploy_workflows.os', must_exist=True),
        Validator('capsule.deploy_arguments', must_exist=True, is_type_of=dict, default={}),
    ],
    libvirt=[
        Validator('libvirt.libvirt_hostname', must_exist=True),
        Validator('libvirt.libvirt_image_dir', default='/var/lib/libvirt/images'),
    ],
    container_repo=[
        Validator(
            'container_repo.registries.redhat.url',
            'container_repo.registries.redhat.username',
            'container_repo.registries.redhat.password',
            'container_repo.registries.redhat.repos_to_sync',
            'container_repo.registries.redhat.long_pass',
            must_exist=True,
        ),
        Validator(
            'container_repo.registries.quay.url',
            'container_repo.registries.quay.username',
            'container_repo.registries.quay.password',
            'container_repo.registries.quay.repos_to_sync',
            must_exist=True,
        ),
    ],
    docker=[
        Validator(
            'docker.external_registry_1',
            'docker.private_registry_url',
            'docker.private_registry_name',
            'docker.private_registry_username',
            'docker.private_registry_password',
            must_exist=True,
        ),
    ],
    ec2=[
        Validator('ec2.access_key', 'ec2.secret_key', 'ec2.region', must_exist=True),
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
            'git.github_token',
            'git.ssh_port',
            'git.http_port',
            'git.hostname',
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
        ),
    ],
    ipa=[
        Validator(
            'ipa.hostname',
            'ipa.username',
            'ipa.password',
            'ipa.basedn',
            'ipa.grpbasedn',
            'ipa.user',
            'ipa.otp_user',
            'ipa.disabled_ipa_user',
            'ipa.group_users',
            'ipa.groups',
            'ipa.keytab_url',
            'ipa.time_based_secret',
            must_exist=True,
        ),
    ],
    jira=[
        Validator('jira.url', default='https://issues.redhat.com'),
        Validator('jira.api_key', must_exist=True),
        Validator('jira.comment_type', default="group"),
        Validator('jira.comment_visibility', default="Red Hat Employee"),
        Validator('jira.enable_comment', default=False),
        Validator('jira.issue_status', default=["Review", "Release Pending"]),
    ],
    ldap=[
        Validator(
            'ldap.basedn',
            'ldap.grpbasedn',
            'ldap.hostname',
            'ldap.nameserver',
            'ldap.realm',
            'ldap.username',
            'ldap.password',
            'ldap.workgroup',
            must_exist=True,
        ),
    ],
    ohsnap=[
        Validator(
            'ohsnap.host',
            'ohsnap.request_retry.timeout',
            'ohsnap.request_retry.delay',
            must_exist=True,
        ),
    ],
    open_ldap=[
        Validator(
            'open_ldap.base_dn',
            'open_ldap.group_base_dn',
            'open_ldap.hostname',
            'open_ldap.username',
            'open_ldap.password',
            'open_ldap.open_ldap_user',
            must_exist=True,
        ),
    ],
    oscap=[
        Validator(
            'oscap.content_path',
            must_exist=True,
        ),
        Validator(
            'oscap.profile',
            default='security7',
            must_exist=True,
        ),
    ],
    osp=[
        Validator(
            'osp.hostname',
            'osp.username',
            'osp.password',
            'osp.tenant',
            'osp.security_group',
            'osp.vm_name',
            'osp.project_domain_id',
            must_exist=True,
        ),
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
    rh_cloud=[Validator('rh_cloud.token', required=True)],
    repos=[
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
            must_exist=True,
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
            'rhev.ca_cert',
            'rhev.image_name',
            must_exist=True,
        ),
    ],
    rhsso=[
        Validator(
            'rhsso.host_name',
            'rhsso.host_url',
            'rhsso.rhsso_user',
            'rhsso.rhsso_password',
            'rhsso.realm',
            'rhsso.totp_secret',
            must_exist=True,
        ),
    ],
    remotedb=[
        Validator(
            'remotedb.server',
            'remotedb.db_server',
            'remotedb.db_password',
            must_exist=True,
        ),
        Validator('remotedb.foreman.username', default='foreman'),
        Validator('remotedb.foreman.db_name', default='foreman'),
        Validator('remotedb.candlepin.username', default='candlepin'),
        Validator('remotedb.candlepin.db_name', default='candlepin'),
        Validator('remotedb.pulp.username', default='pulp'),
        Validator('remotedb.pulp.db_name', default='pulpcore'),
        Validator('remotedb.ssl', default=True),
        Validator('remotedb.port', default=5432),
    ],
    robottelo=[
        Validator('robottelo.settings.ignore_validation_errors', is_type_of=bool, default=False),
        Validator('robottelo.rhel_source', default='ga', is_in=['ga', 'internal']),
        Validator(
            'robottelo.sat_non_ga_versions',
            is_type_of=list,
            default=[],
            cast=lambda x: list(map(str, x)),
        ),
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
    vmware=[
        Validator(
            'vmware.vcenter7.hostname',
            'vmware.vcenter7.hypervisor',
            'vmware.vcenter7.mac_address',
            'vmware.vcenter8.hostname',
            'vmware.vcenter8.hypervisor',
            'vmware.vcenter8.mac_address',
            'vmware.username',
            'vmware.password',
            'vmware.datacenter',
            'vmware.vm_name',
            'vmware.image_os',
            must_exist=True,
        ),
    ],
)
