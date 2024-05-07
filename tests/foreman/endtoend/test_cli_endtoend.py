"""Smoke tests for the ``CLI`` end-to-end scenario.

:Requirement: Cli Endtoend

:CaseAutomation: Automated

:CaseComponent: Hammer

:Team: Endeavour

:CaseImportance: High

"""

from fauxfactory import gen_alphanumeric, gen_ipaddr
import pytest

from robottelo import constants
from robottelo.config import setting_is_set, settings
from robottelo.constants.repos import CUSTOM_RPM_REPO


@pytest.fixture(scope='module')
def fake_manifest_is_set():
    return setting_is_set('fake_manifest')


@pytest.mark.tier1
@pytest.mark.upgrade
def test_positive_cli_find_default_org(module_target_sat):
    """Check if 'Default Organization' is present

    :id: 95ffeb7a-134e-4273-bccc-fe8a3a336b2a

    :expectedresults: 'Default Organization' is found
    """
    result = module_target_sat.cli.Org.info({'name': constants.DEFAULT_ORG})
    assert result['name'] == constants.DEFAULT_ORG


@pytest.mark.tier1
@pytest.mark.upgrade
def test_positive_cli_find_default_loc(module_target_sat):
    """Check if 'Default Location' is present

    :id: 11cf0d06-78ff-47e8-9d50-407a2ea31988

    :expectedresults: 'Default Location' is found
    """
    result = module_target_sat.cli.Location.info({'name': constants.DEFAULT_LOC})
    assert result['name'] == constants.DEFAULT_LOC


@pytest.mark.tier1
@pytest.mark.upgrade
def test_positive_cli_find_admin_user(module_target_sat):
    """Check if Admin User is present

    :id: f6755189-05a6-4d2f-a3b8-98be0cfacaee

    :expectedresults: Admin User is found and has Admin role
    """
    result = module_target_sat.cli.User.info({'login': 'admin'})
    assert result['login'] == 'admin'
    assert result['admin'] == 'yes'


@pytest.mark.no_containers
@pytest.mark.rhel_ver_match('7')
@pytest.mark.tier4
@pytest.mark.e2e
@pytest.mark.upgrade
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_cli_end_to_end(function_entitlement_manifest, target_sat, rhel_contenthost):
    """Perform end to end smoke tests using RH and custom repos.

    1. Create a new user with admin permissions
    2. Using the new user from above
        1. Create a new organization
        2. Clone and upload manifest
        3. Create a new lifecycle environment
        4. Create a custom product
        5. Create a custom YUM repository
        6. Enable a Red Hat repository
        7. Synchronize these two repositories
        8. Create a new content view
        9. Associate the YUM and Red Hat repositories to new content view
        10. Publish content view
        11. Promote content view to the lifecycle environment
        12. Create a new activation key
        13. Add the products to the activation key
        14. Create a new libvirt compute resource
        15. Create a new subnet
        16. Create a new domain
        17. Create a new hostgroup and associate previous entities to it
        18. Provision a client  ** NOT CURRENTLY PROVISIONING

    :id: 8c8b3ffa-0d54-436b-8eeb-1a3542e100a8

    :expectedresults: All tests should succeed and Content should be
        successfully fetched by client.

    :bz: 2216461

    :parametrized: yes
    """
    # step 1: Create a new user with admin permissions
    password = gen_alphanumeric()
    user = target_sat.cli_factory.user({'admin': 'true', 'password': password})
    user['password'] = password

    # step 2.1: Create a new organization
    org = _create(user, target_sat.cli.Org, {'name': gen_alphanumeric()})
    target_sat.cli.SimpleContentAccess.disable({'organization-id': org['id']})

    # step 2.2: Clone and upload manifest
    target_sat.put(f'{function_entitlement_manifest.path}', f'{function_entitlement_manifest.name}')
    target_sat.cli.Subscription.upload(
        {'file': f'{function_entitlement_manifest.name}', 'organization-id': org['id']}
    )

    # step 2.3: Create a new lifecycle environment
    lifecycle_environment = _create(
        user,
        target_sat.cli.LifecycleEnvironment,
        {'name': gen_alphanumeric(), 'organization-id': org['id'], 'prior': 'Library'},
    )

    # step 2.4: Create a custom product
    product = _create(
        user, target_sat.cli.Product, {'name': gen_alphanumeric(), 'organization-id': org['id']}
    )
    repositories = []

    # step 2.5: Create custom YUM repository
    custom_repo = _create(
        user,
        target_sat.cli.Repository,
        {
            'content-type': 'yum',
            'name': gen_alphanumeric(),
            'product-id': product['id'],
            'publish-via-http': 'true',
            'url': CUSTOM_RPM_REPO,
        },
    )
    repositories.append(custom_repo)

    # step 2.6: Enable a Red Hat repository
    target_sat.cli.RepositorySet.enable(
        {
            'basearch': 'x86_64',
            'name': constants.REPOSET['rhst7'],
            'organization-id': org['id'],
            'product': constants.PRDS['rhel'],
            'releasever': None,
        }
    )
    rhel_repo = target_sat.cli.Repository.info(
        {
            'name': constants.REPOS['rhst7']['name'],
            'organization-id': org['id'],
            'product': constants.PRDS['rhel'],
        }
    )
    repositories.append(rhel_repo)

    # step 2.7: Synchronize these two repositories
    for repo in repositories:
        target_sat.cli.Repository.with_user(user['login'], user['password']).synchronize(
            {'id': repo['id']}
        )

    # step 2.8: Create content view
    content_view = _create(
        user, target_sat.cli.ContentView, {'name': gen_alphanumeric(), 'organization-id': org['id']}
    )

    # step 2.9: Associate the YUM and Red Hat repositories to new content view
    for repo in repositories:
        target_sat.cli.ContentView.add_repository(
            {
                'id': content_view['id'],
                'organization-id': org['id'],
                'repository-id': repo['id'],
            }
        )

    # step 2.10: Publish content view
    target_sat.cli.ContentView.with_user(user['login'], user['password']).publish(
        {'id': content_view['id']}
    )

    # step 2.11: Promote content view to the lifecycle environment
    content_view = target_sat.cli.ContentView.with_user(user['login'], user['password']).info(
        {'id': content_view['id']}
    )
    assert len(content_view['versions']) == 1
    cv_version = target_sat.cli.ContentView.with_user(user['login'], user['password']).version_info(
        {'id': content_view['versions'][0]['id']}
    )
    assert len(cv_version['lifecycle-environments']) == 1
    target_sat.cli.ContentView.with_user(user['login'], user['password']).version_promote(
        {'id': cv_version['id'], 'to-lifecycle-environment-id': lifecycle_environment['id']}
    )
    # check that content view exists in lifecycle
    content_view = target_sat.cli.ContentView.with_user(user['login'], user['password']).info(
        {'id': content_view['id']}
    )
    assert len(content_view['versions']) == 1
    cv_version = target_sat.cli.ContentView.with_user(user['login'], user['password']).version_info(
        {'id': content_view['versions'][0]['id']}
    )
    assert len(cv_version['lifecycle-environments']) == 2
    assert cv_version['lifecycle-environments'][-1]['id'] == lifecycle_environment['id']

    # step 2.12: Create a new activation key
    activation_key = _create(
        user,
        target_sat.cli.ActivationKey,
        {
            'content-view-id': content_view['id'],
            'lifecycle-environment-id': lifecycle_environment['id'],
            'name': gen_alphanumeric(),
            'organization-id': org['id'],
        },
    )

    # step 2.13: Add the products to the activation key
    subscription_list = target_sat.cli.Subscription.with_user(user['login'], user['password']).list(
        {'organization-id': org['id']}, per_page=False
    )
    for subscription in subscription_list:
        if subscription['name'] == constants.DEFAULT_SUBSCRIPTION_NAME:
            target_sat.cli.ActivationKey.with_user(
                user['login'], user['password']
            ).add_subscription(
                {
                    'id': activation_key['id'],
                    'quantity': 1,
                    'subscription-id': subscription['id'],
                }
            )

    # step 2.13.1: Enable product content
    target_sat.cli.ActivationKey.with_user(user['login'], user['password']).content_override(
        {
            'content-label': constants.REPOS['rhst7']['id'],
            'id': activation_key['id'],
            'organization-id': org['id'],
            'value': '1',
        }
    )

    # BONUS: Create a content host and associate it with promoted
    # content view and last lifecycle where it exists
    content_host_name = gen_alphanumeric()
    content_host = target_sat.cli.Host.with_user(
        user['login'], user['password']
    ).subscription_register(
        {
            'content-view-id': content_view['id'],
            'lifecycle-environment-id': lifecycle_environment['id'],
            'name': content_host_name,
            'organization-id': org['id'],
        }
    )

    content_host = target_sat.cli.Host.with_user(user['login'], user['password']).info(
        {'id': content_host['id']}, output_format='json'
    )

    # check that content view matches what we passed
    assert (
        content_host['content-information']['content-view-environments']['1']['content-view'][
            'name'
        ]
        == content_view['name']
    )

    # check that lifecycle environment matches
    assert (
        content_host['content-information']['content-view-environments']['1'][
            'lifecycle-environment'
        ]['name']
        == lifecycle_environment['name']
    )

    # step 2.14: Create a new libvirt compute resource
    _create(
        user,
        target_sat.cli.ComputeResource,
        {
            'name': gen_alphanumeric(),
            'provider': 'Libvirt',
            'url': f'qemu+ssh://root@{settings.libvirt.libvirt_hostname}/system',
        },
    )

    # step 2.15: Create a new subnet
    subnet = _create(
        user,
        target_sat.cli.Subnet,
        {
            'name': gen_alphanumeric(),
            'network': gen_ipaddr(ip3=True),
            'mask': '255.255.255.0',
        },
    )

    # step 2.16: Create a new domain
    domain = _create(user, target_sat.cli.Domain, {'name': gen_alphanumeric()})

    # step 2.17: Create a new hostgroup and associate previous entities to it
    host_group = _create(
        user,
        target_sat.cli.HostGroup,
        {'domain-id': domain['id'], 'name': gen_alphanumeric(), 'subnet-id': subnet['id']},
    )
    target_sat.cli.HostGroup.with_user(user['login'], user['password']).update(
        {
            'id': host_group['id'],
            'organization-ids': org['id'],
            'content-view-id': content_view['id'],
            'lifecycle-environment-id': lifecycle_environment['id'],
        }
    )

    # step 2.18: Provision a client
    # TODO this isn't provisioning through satellite as intended
    # Note it wasn't well before the change that added this todo
    rhel_contenthost.install_katello_ca(target_sat)
    # Register client with foreman server using act keys
    rhel_contenthost.register_contenthost(org['label'], activation_key['name'])
    assert rhel_contenthost.subscribed
    # Install rpm on client
    package_name = 'katello-agent'
    result = rhel_contenthost.execute(f'yum install -y {package_name}')
    assert result.status == 0
    # Verify that the package is installed by querying it
    result = rhel_contenthost.run(f'rpm -q {package_name}')
    assert result.status == 0


def _create(user, entity, attrs):
    """Creates a Foreman entity and returns it.

    :param dict user: A python dictionary representing a User
    :param object entity: A valid CLI entity.
    :param dict attrs: A python dictionary with attributes to use when
        creating entity.
    :return: A ``dict`` representing the Foreman entity.
    :rtype: dict
    """
    # Create new entity as new user
    return entity.with_user(user['login'], user['password']).create(attrs)
