"""CLI Tests for the errata management feature

:Requirement: Errata

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: ErrataManagement

:Assignee: akjha

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from datetime import date
from datetime import datetime
from datetime import timedelta
from operator import itemgetter

import pytest
from broker.broker import VMBroker
from fauxfactory import gen_string
from nailgun import entities

from robottelo.api.utils import enable_rhrepo_and_fetchid
from robottelo.api.utils import wait_for_tasks
from robottelo.cli.activationkey import ActivationKey
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.contentview import ContentView
from robottelo.cli.contentview import ContentViewFilter
from robottelo.cli.erratum import Erratum
from robottelo.cli.factory import make_content_view_filter
from robottelo.cli.factory import make_content_view_filter_rule
from robottelo.cli.factory import make_filter
from robottelo.cli.factory import make_host_collection
from robottelo.cli.factory import make_repository
from robottelo.cli.factory import make_role
from robottelo.cli.factory import make_user
from robottelo.cli.factory import setup_org_for_a_custom_repo
from robottelo.cli.factory import setup_org_for_a_rh_repo
from robottelo.cli.filter import Filter
from robottelo.cli.host import Host
from robottelo.cli.hostcollection import HostCollection
from robottelo.cli.org import Org
from robottelo.cli.package import Package
from robottelo.cli.repository import Repository
from robottelo.cli.repository_set import RepositorySet
from robottelo.cli.task import Task
from robottelo.cli.user import User
from robottelo.config import settings
from robottelo.constants import DEFAULT_ARCHITECTURE
from robottelo.constants import DEFAULT_CV
from robottelo.constants import DEFAULT_SUBSCRIPTION_NAME
from robottelo.constants import DISTRO_RHEL7
from robottelo.constants import FAKE_1_CUSTOM_PACKAGE
from robottelo.constants import FAKE_2_CUSTOM_PACKAGE
from robottelo.constants import FAKE_2_CUSTOM_PACKAGE_NAME
from robottelo.constants import FAKE_4_CUSTOM_PACKAGE
from robottelo.constants import FAKE_4_CUSTOM_PACKAGE_NAME
from robottelo.constants import FAKE_5_CUSTOM_PACKAGE
from robottelo.constants import PRDS
from robottelo.constants import REAL_0_ERRATA_ID
from robottelo.constants import REAL_4_ERRATA_CVES
from robottelo.constants import REAL_4_ERRATA_ID
from robottelo.constants import REAL_RHEL7_0_2_PACKAGE_NAME
from robottelo.constants import REPOS
from robottelo.constants import REPOSET
from robottelo.hosts import ContentHost

PER_PAGE = 10
PER_PAGE_LARGE = 1000
ERRATA = [
    {
        'id': settings.repos.yum_6.errata[2],  # security advisory
        'old_package': FAKE_1_CUSTOM_PACKAGE,
        'new_package': FAKE_2_CUSTOM_PACKAGE,
        'package_name': FAKE_2_CUSTOM_PACKAGE_NAME,
    },
    {
        'id': settings.repos.yum_6.errata[0],  # bugfix advisory
        'old_package': FAKE_4_CUSTOM_PACKAGE,
        'new_package': FAKE_5_CUSTOM_PACKAGE,
        'package_name': FAKE_4_CUSTOM_PACKAGE_NAME,
    },
]
REPO_WITH_ERRATA = {
    'url': settings.repos.yum_9.url,
    'errata': ERRATA,
    'errata_ids': settings.repos.yum_9.errata,
}
REPOS_WITH_ERRATA = (
    {
        'url': settings.repos.yum_9.url,
        'errata_count': len(settings.repos.yum_9.errata),
        'org_errata_count': len(settings.repos.yum_9.errata),
        'errata_id': settings.repos.yum_9.errata[0],
    },
    {
        'url': settings.repos.yum_1.url,
        'errata_count': len(settings.repos.yum_1.errata),
        'org_errata_count': len(settings.repos.yum_1.errata),
        'errata_id': settings.repos.yum_0.errata[1],
    },
    {
        'url': settings.repos.yum_2.url,
        'errata_count': len(settings.repos.yum_2.errata),
        'org_errata_count': len(settings.repos.yum_2.errata) + len(settings.repos.yum_3.errata),
        'errata_id': settings.repos.yum_0.errata[0],
    },
    {
        'url': settings.repos.yum_3.url,
        'errata_count': len(settings.repos.yum_3.errata),
        'org_errata_count': len(settings.repos.yum_2.errata) + len(settings.repos.yum_3.errata),
        'errata_id': settings.repos.yum_3.errata[5],
    },
)

TIMESTAMP_FMT = '%Y-%m-%d %H:%M'

PSUTIL_RPM = 'python2-psutil-5.6.7-1.el7.x86_64.rpm'

pytestmark = [
    pytest.mark.skipif(
        (not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url'
    ),
    pytest.mark.run_in_one_thread,
]


@pytest.fixture(scope='module')
def orgs():
    """Create and return a list of three orgs."""
    return [entities.Organization().create() for _ in range(3)]


@pytest.fixture(scope='module')
def products_with_repos(orgs):
    """Create and return a list of products. For each product, create and sync a single repo."""
    products = []
    # Create one product for each org, and a second product for the last org.
    for org, params in zip(orgs + orgs[-1:], REPOS_WITH_ERRATA):
        product = entities.Product(organization=org).create()
        # Replace the organization entity returned by create(), which contains only the id,
        # with the one we already have.
        product.organization = org
        products.append(product)
        repo = make_repository(
            {
                'download-policy': 'immediate',
                'organization-id': product.organization.id,
                'product-id': product.id,
                'url': params['url'],
            }
        )
        Repository.synchronize({'id': repo['id']})

    return products


@pytest.fixture(scope='module')
def rh_repo(module_org, module_lce, module_cv, module_ak_cv_lce):
    """Add a subscription for the Satellite Tools repo to activation key."""
    setup_org_for_a_rh_repo(
        {
            'product': PRDS['rhel'],
            'repository-set': REPOSET['rhst7'],
            'repository': REPOS['rhst7']['name'],
            'organization-id': module_org.id,
            'content-view-id': module_cv.id,
            'lifecycle-environment-id': module_lce.id,
            'activationkey-id': module_ak_cv_lce.id,
        },
        force_manifest_upload=True,
    )


@pytest.fixture(scope='module')
def custom_repo(module_org, module_lce, module_cv, module_ak_cv_lce):
    """Create custom repo and add a subscription to activation key."""
    setup_org_for_a_custom_repo(
        {
            'url': REPO_WITH_ERRATA['url'],
            'organization-id': module_org.id,
            'content-view-id': module_cv.id,
            'lifecycle-environment-id': module_lce.id,
            'activationkey-id': module_ak_cv_lce.id,
        }
    )


@pytest.fixture(scope='module')
def hosts(request):
    """Deploy hosts via broker."""
    num_hosts = getattr(request, 'param', 2)
    with VMBroker(nick=DISTRO_RHEL7, host_classes={'host': ContentHost}, _count=num_hosts) as hosts:
        if type(hosts) is not list or len(hosts) != num_hosts:
            pytest.fail('Failed to provision the expected number of hosts.')
        yield hosts


@pytest.fixture(scope='module')
def register_hosts(hosts, module_org, module_ak_cv_lce, rh_repo, custom_repo):
    """Register hosts to Satellite and install katello-agent rpm."""
    for host in hosts:
        host.install_katello_ca()
        host.register_contenthost(module_org.name, module_ak_cv_lce.name)
        host.enable_repo(REPOS['rhst7']['id'])
        host.install_katello_agent()
    return hosts


@pytest.fixture
def errata_hosts(register_hosts):
    """Ensure that rpm is installed on host."""
    for host in register_hosts:
        # Remove all packages.
        for errata in REPO_WITH_ERRATA['errata']:
            # Remove package if present, old or new.
            package_name = errata['package_name']
            result = host.execute(f'yum erase -y {package_name}')
            if result.status != 0:
                pytest.fail(f'Failed to remove {package_name}: {result.stdout} {result.stderr}')

            # Install old package, so that errata apply.
            old_package = errata['old_package']
            result = host.execute(f'yum install -y {old_package}')
            if result.status != 0:
                pytest.fail(f'Failed to install {old_package}: {result.stdout} {result.stderr}')
    return register_hosts


@pytest.fixture(scope='module')
def host_collection(module_org, module_ak_cv_lce, register_hosts):
    """Create and setup host collection."""
    host_collection = make_host_collection({'organization-id': module_org.id})
    host_ids = [Host.info({'name': host.hostname})['id'] for host in register_hosts]
    HostCollection.add_host(
        {
            'id': host_collection['id'],
            'organization-id': module_org.id,
            'host-ids': host_ids,
        }
    )
    ActivationKey.add_host_collection(
        {
            'id': module_ak_cv_lce.id,
            'host-collection-id': host_collection['id'],
            'organization-id': module_org.id,
        }
    )
    return host_collection


def is_rpm_installed(host, rpm=None):
    """Return whether the specified rpm is installed.

    :type host: robottelo.hosts.ContentHost instance
    :type rpm: str
    :rtype: bool
    """
    rpm = rpm or REPO_WITH_ERRATA['errata'][0]['new_package']
    return not host.execute(f'rpm -q {rpm}').status


def get_sorted_errata_info_by_id(errata_ids, sort_by='issued', sort_reversed=False):
    """Query hammer for erratum ids info

    :param errata_ids: a list of errata id
    :param sort_by: the field to sort by the results (issued or updated)
    :param sort_reversed: whether the sort should be reversed
            (not ascending)
    :return: a list of errata info dict for each errata id in errata_ids
    :type errata_ids: list[str]
    :type sort_by: str
    :type sort_reversed: bool
    :rtype: list[dict]
    """
    if len(errata_ids) > PER_PAGE:
        raise Exception('Errata ids length exceeded')
    errata_info = [
        Erratum.info(options={'id': errata_id}, output_format='json') for errata_id in errata_ids
    ]
    return sorted(errata_info, key=itemgetter(sort_by), reverse=sort_reversed)


def get_errata_ids(*params):
    """Return list of sets of errata ids corresponding to the provided params."""
    errata_ids = [{errata['errata-id'] for errata in Erratum.list(param)} for param in params]
    return errata_ids[0] if len(errata_ids) == 1 else errata_ids


def check_errata(errata_ids, by_org=False):
    """Verify that each list of errata ids matches the expected values

    :param errata_ids: a list containing a list of errata ids for each repo
    :type errata_ids: list[list]
    """
    for ids, repo_with_errata in zip(errata_ids, REPOS_WITH_ERRATA):
        assert len(ids) == repo_with_errata['org_errata_count' if by_org else 'errata_count']
        assert repo_with_errata['errata_id'] in ids


def filter_sort_errata(org, sort_by_date='issued', filter_by_org=None):
    """Compare the list of errata returned by `hammer erratum {list|info}` to the expected
    values, subject to the date sort and organization filter options.

    :param org: organization instance
    :type org: entities.Organization
    :param sort_by_date: date sort method
    :type sort_by_date: str ('issued', 'updated'). Default: 'issued'
    :param filter_by_org: organization selection method
    :type filter_by_org str ('id', 'name', 'label') or None. Default: None
    """
    for sort_order in ('ASC', 'DESC'):
        list_param = {'order': f'{sort_by_date} {sort_order}', 'per-page': PER_PAGE}

        if filter_by_org == 'id':
            list_param['organization-id'] = org.id
        elif filter_by_org == 'name':
            list_param['organization'] = org.name
        elif filter_by_org == 'label':
            list_param['organization-label'] = org.label

        sort_reversed = True if sort_order == 'DESC' else False

        errata_list = Erratum.list(list_param)
        assert len(errata_list) > 0

        # Build a sorted errata info list, which also contains the sort field.
        errata_internal_ids = [errata['id'] for errata in errata_list]
        sorted_errata_info = get_sorted_errata_info_by_id(
            errata_internal_ids, sort_by=sort_by_date, sort_reversed=sort_reversed
        )

        sort_field_values = [errata[sort_by_date] for errata in sorted_errata_info]
        assert sort_field_values == sorted(sort_field_values, reverse=sort_reversed)

        errata_ids = [errata['errata-id'] for errata in errata_list]
        sorted_errata_ids = [errata['errata-id'] for errata in sorted_errata_info]
        assert errata_ids == sorted_errata_ids


def cv_publish_promote(cv, org, lce):
    """Publish and promote a new version into the given lifecycle environment.

    :param cv: content view
    :type cv: entities.ContentView
    :param org: organization
    :type org: entities.Organization
    :param lce: lifecycle environment
    :type lce: entities.LifecycleEnvironment
    """
    ContentView.publish({'id': cv.id})
    cvv = ContentView.info({'id': cv.id})['versions'][-1]
    ContentView.version_promote(
        {
            'id': cvv['id'],
            'organization-id': org.id,
            'to-lifecycle-environment-id': lce.id,
        }
    )


def cv_filter_cleanup(filter_id, cv, org, lce):
    """Delete the cv filter, then publish and promote an unfiltered version."""
    ContentViewFilter.delete(
        {
            'content-view-id': cv.id,
            'id': filter_id,
            'organization-id': org.id,
        }
    )
    cv_publish_promote(cv, org, lce)


@pytest.mark.tier3
@pytest.mark.parametrize('filter_by_hc', ('id', 'name'), ids=('hc_id', 'hc_name'))
@pytest.mark.parametrize(
    'filter_by_org', ('id', 'name', 'label'), ids=('org_id', 'org_name', 'org_label')
)
def test_positive_install_by_host_collection_and_org(
    module_org, host_collection, errata_hosts, filter_by_hc, filter_by_org
):
    """Use host collection id or name and org id, name, or label to install an update on the host
    collection.

    :id: 1b063f76-c85f-42fb-a919-5de319b09b99

    :parametrized: yes

    :Setup: Errata synced on satellite server.

    :Steps: host-collection erratum install --errata <errata>
        (--id <hc_id>|--name <hc_name>)
        (--organization-id <org_id>|--organization <org_name>|--organization-label <org_label>)

    :expectedresults: Erratum is installed.

    :CaseLevel: System

    :BZ: 1457977
    """
    param = {'errata': [REPO_WITH_ERRATA['errata'][0]['id']]}

    if filter_by_hc == 'id':
        param['id'] = host_collection['id']
    elif filter_by_hc == 'name':
        param['name'] = host_collection['name']

    if filter_by_org == 'id':
        param['organization-id'] = module_org.id
    elif filter_by_org == 'name':
        param['organization'] = module_org.name
    elif filter_by_org == 'label':
        param['organization-label'] = module_org.label

    install_task = HostCollection.erratum_install(param)
    Task.progress({'id': install_task[0]['id']})
    for host in errata_hosts:
        assert is_rpm_installed(host)


@pytest.mark.tier3
def test_negative_install_by_hc_id_without_errata_info(module_org, host_collection, errata_hosts):
    """Attempt to install an erratum on a host collection by host collection id but no errata info
    specified.

    :id: 3635698d-4f09-4a60-91ea-1957e5949750

    :Setup: Errata synced on satellite server.

    :Steps: host-collection erratum install --id <id> --organization-id
        <org_id>

    :expectedresults: Error message thrown.

    :CaseImportance: Low

    :CaseLevel: System
    """
    with pytest.raises(CLIReturnCodeError, match="Error: Option '--errata' is required"):
        HostCollection.erratum_install(
            {'id': host_collection['id'], 'organization-id': module_org.id}
        )


@pytest.mark.tier3
def test_negative_install_by_hc_name_without_errata_info(module_org, host_collection, errata_hosts):
    """Attempt to install an erratum on a host collection by host collection name but no errata
    info specified.

    :id: 12d78bca-efd1-407a-9bd3-f989c2bda6a8

    :Setup: Errata synced on satellite server.

    :Steps: host-collection erratum install --name <name> --organization-id
        <org_id>

    :expectedresults: Error message thrown.

    :CaseImportance: Low

    :CaseLevel: System
    """
    with pytest.raises(CLIReturnCodeError, match="Error: Option '--errata' is required"):
        HostCollection.erratum_install(
            {'name': host_collection['name'], 'organization-id': module_org.id}
        )


@pytest.mark.tier3
def test_negative_install_without_hc_info(module_org, host_collection):
    """Attempt to install an erratum on a host collection without specifying host collection info.
    This test only works with two or more host collections (BZ#1928281).
    We have the one from the fixture, just need to create one more at the start of the test.

    :id: 753d36f0-d19b-494d-a247-ce2d61c4cf74

    :Setup: Errata synced on satellite server.

    :Steps: host-collection erratum install --errata <errata>
        --organization-id <org_id>

    :expectedresults: Error message thrown.

    :BZ: 1928281

    :CaseImportance: Low

    :CaseLevel: System
    """
    make_host_collection({'organization-id': module_org.id})
    with pytest.raises(CLIReturnCodeError):
        HostCollection.erratum_install(
            {'organization-id': module_org.id, 'errata': [REPO_WITH_ERRATA['errata'][0]['id']]}
        )


@pytest.mark.tier3
def test_negative_install_by_hc_id_without_org_info(module_org, host_collection):
    """Attempt to install an erratum on a host collection by host collection id but without
    specifying any org info.

    :id: b7d32bb3-9c5f-452b-b421-f8e9976ca52c

    :Setup: Errata synced on satellite server.

    :Steps: host-collection erratum install --errata <errata> --id <id>

    :expectedresults: Error message thrown.

    :CaseImportance: Low

    :CaseLevel: System
    """
    with pytest.raises(CLIReturnCodeError, match='Error: Could not find organization'):
        HostCollection.erratum_install(
            {'id': host_collection['id'], 'errata': [REPO_WITH_ERRATA['errata'][0]['id']]}
        )


@pytest.mark.tier3
def test_negative_install_by_hc_name_without_org_info(module_org, host_collection):
    """Attempt to install an erratum on a host collection by host collection name but without
    specifying any org info.

    :id: 991f5b61-a4d1-444c-8a21-8ffe48e83f76

    :Setup: Errata synced on satellite server.

    :Steps: host-collection erratum install --errata <errata> --name <name>

    :expectedresults: Error message thrown.

    :CaseImportance: Low

    :CaseLevel: System
    """
    with pytest.raises(CLIReturnCodeError, match='Error: Could not find organization'):
        HostCollection.erratum_install(
            {'name': host_collection['name'], 'errata': [REPO_WITH_ERRATA['errata'][0]['id']]}
        )


@pytest.mark.tier3
@pytest.mark.upgrade
def test_positive_list_affected_chosts(module_org, errata_hosts):
    """View a list of affected content hosts for an erratum.

    :id: 3b592253-52c0-4165-9a48-ba55287e9ee9

    :Setup: Errata synced on satellite server, custom package installed on errata hosts.

    :Steps: host list --search 'applicable_errata = <erratum_id>'
        --organization-id=<org_id>

    :expectedresults: List of affected content hosts for an erratum is
        displayed.

    :CaseAutomation: Automated
    """
    result = Host.list(
        {
            'search': f'applicable_errata = {REPO_WITH_ERRATA["errata"][0]["id"]}',
            'organization-id': module_org.id,
            'fields': 'Name',
        }
    )
    reported_hostnames = {item['name'] for item in result}
    hostnames = {host.hostname for host in errata_hosts}
    assert hostnames.issubset(
        reported_hostnames
    ), 'One or more hostnames not found in list of applicable hosts'


@pytest.mark.tier3
def test_install_errata_to_one_host(module_org, errata_hosts, host_collection):
    """Install an erratum to one of the hosts in a host collection.

    :id: bfcee2de-3448-497e-a696-fcd30cea9d33

    :expectedresults: Errata was successfully installed in only one of the hosts in
        the host collection

    :Setup: Errata synced on satellite server, custom package installed on errata hosts.

    :Steps:
        1. Remove packages from one host.
        2. host-collection erratum install --errata <errata> --id <id>
            --organization <org_name>
        3. Assert first host does not have the package.
        4. Assert second host does have the new package.


    :expectedresults: Erratum is only installed on one host.

    :BZ: 1810774
    """
    errata = REPO_WITH_ERRATA['errata'][0]

    # Remove the package on first host to remove need for errata.
    result = errata_hosts[0].execute(f'yum erase -y {errata["package_name"]}')
    assert result.status == 0, f'Failed to erase the rpm: {result.stdout}'

    # Apply errata to the host collection.
    install_task = HostCollection.erratum_install(
        {
            'id': host_collection['id'],
            'organization': module_org.name,
            'errata': [errata['id']],
        }
    )
    Task.progress({'id': install_task[0]['id']})

    assert not is_rpm_installed(
        errata_hosts[0], rpm=errata['package_name']
    ), 'Package should not be installed on host.'
    assert is_rpm_installed(
        errata_hosts[1], rpm=errata['new_package']
    ), 'Package should be installed on host.'


@pytest.mark.tier3
def test_positive_list_affected_chosts_by_erratum_restrict_flag(
    request, module_org, module_cv, module_lce, errata_hosts
):
    """View a list of affected content hosts for an erratum filtered
    with restrict flags. Applicability is calculated using the Library,
    so that search must not limit to CV or LCE. Installability
    is calculated using the attached CV, subject to the CV's own filtering,
    so that search must limit to CV and LCE.

    :id: 594acd48-892c-499e-b0cb-6506cea7cd64

    :Setup: Errata synced on satellite server, custom package installed on errata hosts.

    :Steps:

        1. erratum list --erratum-id=<erratum_id>
            --organization-id=<org_id> --errata-restrict-installable=1

        2. erratum list --erratum-id=<erratum_id>
            --organization-id=<org_id> --errata-restrict-installable=0

        3. erratum list --erratum-id=<erratum_id>
            --organization-id=<org_id> --errata-restrict-applicable=1

        4. erratum list --erratum-id=<erratum_id>
            --organization-id=<org_id> --errata-restrict-applicable=0


    :expectedresults: List of affected content hosts for an erratum is
        displayed filtered with corresponding restrict flags.

    :CaseAutomation: Automated
    """

    # Uninstall package so that only the first errata applies.
    for host in errata_hosts:
        host.execute(f'yum erase -y {REPO_WITH_ERRATA["errata"][1]["package_name"]}')

    # Create list of uninstallable errata.
    errata = REPO_WITH_ERRATA['errata'][0]
    uninstallable = REPO_WITH_ERRATA['errata_ids'].copy()
    uninstallable.remove(errata['id'])

    # Check search for only installable errata
    param = {
        'errata-restrict-installable': 1,
        'content-view-id': module_cv.id,
        'lifecycle-environment-id': module_lce.id,
        'organization-id': module_org.id,
        'per-page': PER_PAGE_LARGE,
    }
    errata_ids = get_errata_ids(param)
    assert errata['id'] in errata_ids, 'Errata not found in list of installable errata'
    assert not set(uninstallable) & set(errata_ids), 'Unexpected errata found'

    # Check search of errata is not affected by installable=0 restrict flag
    param = {
        'errata-restrict-installable': 0,
        'content-view-id': module_cv.id,
        'lifecycle-environment-id': module_lce.id,
        'organization-id': module_org.id,
        'per-page': PER_PAGE_LARGE,
    }
    errata_ids = get_errata_ids(param)
    assert set(REPO_WITH_ERRATA['errata_ids']).issubset(
        errata_ids
    ), 'Errata not found in list of installable errata'

    # Check list of applicable errata
    param = {
        'errata-restrict-applicable': 1,
        'organization-id': module_org.id,
        'per-page': PER_PAGE_LARGE,
    }
    errata_ids = get_errata_ids(param)
    assert errata['id'] in errata_ids, 'Errata not found in list of applicable errata'

    # Check search of errata is not affected by applicable=0 restrict flag
    param = {
        'errata-restrict-applicable': 0,
        'organization-id': module_org.id,
        'per-page': PER_PAGE_LARGE,
    }
    errata_ids = get_errata_ids(param)
    assert set(REPO_WITH_ERRATA['errata_ids']).issubset(
        errata_ids
    ), 'Errata not found in list of applicable errata'

    # Apply a filter and rule to the CV to hide the RPM, thus making erratum not installable
    # Make RPM exclude filter
    cv_filter = make_content_view_filter(
        {
            'content-view-id': module_cv.id,
            'name': 'erratum_restrict_test',
            'description': 'Hide the installable errata',
            'organization-id': module_org.id,
            'type': 'rpm',
            'inclusion': 'false',
        }
    )

    @request.addfinalizer
    def cleanup():
        cv_filter_cleanup(cv_filter['filter-id'], module_cv, module_org, module_lce)

    # Make rule to hide the RPM that creates the need for the installable erratum
    make_content_view_filter_rule(
        {
            'content-view-id': module_cv.id,
            'content-view-filter-id': cv_filter['filter-id'],
            'name': errata['package_name'],
        }
    )

    # Publish and promote a new version with the filter
    cv_publish_promote(module_cv, module_org, module_lce)

    # Check that the installable erratum is no longer present in the list
    param = {
        'errata-restrict-installable': 0,
        'content-view-id': module_cv.id,
        'lifecycle-environment-id': module_lce.id,
        'organization-id': module_org.id,
        'per-page': PER_PAGE_LARGE,
    }
    errata_ids = get_errata_ids(param)
    assert errata['id'] not in errata_ids, 'Errata not found in list of installable errata'

    # Check errata still applicable
    param = {
        'errata-restrict-applicable': 1,
        'organization-id': module_org.id,
        'per-page': PER_PAGE_LARGE,
    }
    errata_ids = get_errata_ids(param)
    assert errata['id'] in errata_ids, 'Errata not found in list of applicable errata'


@pytest.mark.tier3
def test_host_errata_search_commands(
    request, module_org, module_cv, module_lce, host_collection, errata_hosts
):
    """View a list of affected hosts for security (RHSA) and bugfix (RHBA) errata,
    filtered with errata status and applicable flags. Applicability is calculated using the
    Library, but Installability is calculated using the attached CV, and is subject to the
    CV's own filtering.

    :id: 07757a77-7ab4-4020-99af-2beceb023266

    :Setup: Errata synced on satellite server, custom package installed on errata hosts.

    :Steps:
        1.  host list --search 'errata_status = errata_needed'
        2.  host list --search 'errata_status = security_needed'
        3.  host list --search 'applicable_errata = <bugfix_advisory>'
        4.  host list --search 'applicable_errata = <security_advisory>'
        5.  host list --search 'applicable_rpms = <bugfix_package>'
        6.  host list --search 'applicable_rpms = <security_package>'
        7.  Create filter & rule to hide RPM (applicable vs. installable test)
        8.  Repeat steps 3 and 5, but 5 expects host name not found.


    :expectedresults: The hosts are correctly listed for security and bugfix advisories.
    """
    # note time for later wait_for_tasks include 2 mins margin of safety.
    timestamp = (datetime.utcnow() - timedelta(minutes=2)).strftime(TIMESTAMP_FMT)

    errata = REPO_WITH_ERRATA['errata']

    # Update package on first host so that the security advisory doesn't apply.
    result = errata_hosts[0].execute(f'yum update -y {errata[0]["new_package"]}')
    assert result.status == 0, 'Failed to install rpm'

    # Update package on second host so that the bugfix advisory doesn't apply.
    result = errata_hosts[1].execute(f'yum update -y {errata[1]["new_package"]}')
    assert result.status == 0, 'Failed to install rpm'

    # Wait for upload profile event (in case Satellite system slow)
    host = entities.Host().search(query={'search': f'name={errata_hosts[0].hostname}'})
    wait_for_tasks(
        search_query=(
            'label = Actions::Katello::Host::UploadProfiles'
            f' and resource_id = {host[0].id}'
            f' and started_at >= "{timestamp}"'
        ),
        search_rate=15,
        max_tries=10,
    )

    # Step 1: Search for hosts that require bugfix advisories
    result = Host.list(
        {
            'search': 'errata_status = errata_needed',
            'organization-id': module_org.id,
            'per-page': PER_PAGE_LARGE,
        }
    )
    result = [item['name'] for item in result]
    assert errata_hosts[0].hostname in result
    assert errata_hosts[1].hostname not in result

    # Step 2: Search for hosts that require security advisories
    result = Host.list(
        {
            'search': 'errata_status = security_needed',
            'organization-id': module_org.id,
            'per-page': PER_PAGE_LARGE,
        }
    )
    result = [item['name'] for item in result]
    assert errata_hosts[0].hostname not in result
    assert errata_hosts[1].hostname in result

    # Step 3: Search for hosts that require the specified bugfix advisory
    result = Host.list(
        {
            'search': f'applicable_errata = {errata[1]["id"]}',
            'organization-id': module_org.id,
            'per-page': PER_PAGE_LARGE,
        }
    )
    result = [item['name'] for item in result]
    assert errata_hosts[0].hostname in result
    assert errata_hosts[1].hostname not in result

    # Step 4: Search for hosts that require the specified security advisory
    result = Host.list(
        {
            'search': f'applicable_errata = {errata[0]["id"]}',
            'organization-id': module_org.id,
            'per-page': PER_PAGE_LARGE,
        }
    )
    result = [item['name'] for item in result]
    assert errata_hosts[0].hostname not in result
    assert errata_hosts[1].hostname in result

    # Step 5: Search for hosts that require the specified bugfix package
    result = Host.list(
        {
            'search': f'applicable_rpms = {errata[1]["new_package"]}',
            'organization-id': module_org.id,
            'per-page': PER_PAGE_LARGE,
        }
    )
    result = [item['name'] for item in result]
    assert errata_hosts[0].hostname in result
    assert errata_hosts[1].hostname not in result

    # Step 6: Search for hosts that require the specified security package
    result = Host.list(
        {
            'search': f'applicable_rpms = {errata[0]["new_package"]}',
            'organization-id': module_org.id,
            'per-page': PER_PAGE_LARGE,
        }
    )
    result = [item['name'] for item in result]
    assert errata_hosts[0].hostname not in result
    assert errata_hosts[1].hostname in result

    # Step 7: Apply filter and rule to CV to hide RPM, thus making erratum not installable
    # Make RPM exclude filter
    cv_filter = make_content_view_filter(
        {
            'content-view-id': module_cv.id,
            'name': 'erratum_search_test',
            'description': 'Hide the installable errata',
            'organization-id': module_org.id,
            'type': 'rpm',
            'inclusion': 'false',
        }
    )

    @request.addfinalizer
    def cleanup():
        cv_filter_cleanup(cv_filter['filter-id'], module_cv, module_org, module_lce)

    # Make rule to exclude the specified bugfix package
    make_content_view_filter_rule(
        {
            'content-view-id': module_cv.id,
            'content-view-filter-id': cv_filter['filter-id'],
            'name': errata[1]['package_name'],
        }
    )

    # Publish and promote a new version with the filter
    cv_publish_promote(module_cv, module_org, module_lce)

    # Step 8: Run tests again. Applicable should still be true, installable should now be false.
    # Search for hosts that require the bugfix package.
    result = Host.list(
        {
            'search': f'applicable_rpms = {errata[1]["new_package"]}',
            'organization-id': module_org.id,
            'per-page': PER_PAGE_LARGE,
        }
    )
    result = [item['name'] for item in result]
    assert errata_hosts[0].hostname in result
    assert errata_hosts[1].hostname not in result

    # Search for hosts that require the specified bugfix advisory.
    result = Host.list(
        {
            'search': f'installable_errata = {errata[1]["id"]}',
            'organization-id': module_org.id,
            'per-page': PER_PAGE_LARGE,
        }
    )
    result = [item['name'] for item in result]
    assert errata_hosts[0].hostname not in result
    assert errata_hosts[1].hostname not in result


@pytest.mark.tier3
@pytest.mark.parametrize('sort_by_date', ('issued', 'updated'), ids=('issued_date', 'updated_date'))
@pytest.mark.parametrize(
    'filter_by_org',
    ('id', 'name', 'label', None),
    ids=('org_id', 'org_name', 'org_label', 'no_org_filter'),
)
def test_positive_list_filter_by_org_sort_by_date(
    module_org, rh_repo, custom_repo, filter_by_org, sort_by_date
):
    """Filter by organization and sort by date.

    :id: 248af10f-917c-477d-a481-43f584692c69

    :parametrized: yes

    :Setup: Errata synced on satellite server.

    :Steps: erratum list
         (--organization-id=<org_id>|--organization=<org_name>|--organization-label=<org_label>)
         --order ('updated ASC'|'updated DESC'|'issued ASC'|'issued DESC')

    :expectedresults: Errata are filtered by org and sorted by date.
    """
    filter_sort_errata(module_org, sort_by_date=sort_by_date, filter_by_org=filter_by_org)


@pytest.mark.tier3
def test_positive_list_filter_by_product_id(products_with_repos):
    """Filter errata by product id

    :id: 7d06950a-c058-48b3-a384-c3565cbd643f

    :Setup: Errata synced on satellite server.

    :Steps: erratum list --product-id=<productid>

    :expectedresults: Errata is filtered by product id.
    """
    params = [
        {'product-id': product.id, 'per-page': PER_PAGE_LARGE} for product in products_with_repos
    ]
    errata_ids = get_errata_ids(*params)
    check_errata(errata_ids)


@pytest.mark.tier3
@pytest.mark.parametrize('filter_by_product', ('id', 'name'), ids=('product_id', 'product_name'))
@pytest.mark.parametrize(
    'filter_by_org', ('id', 'name', 'label'), ids=('org_id', 'org_name', 'org_label')
)
def test_positive_list_filter_by_product_and_org(
    products_with_repos, filter_by_product, filter_by_org
):
    """Filter errata by product id and Org id

    :id: ca0e8210-aecb-424a-b39f-24db24461312

    :parametrized: yes

    :Setup: Errata synced on satellite server.

    :Steps: erratum list (--product-id=<product_id>|--product=<product_name>)
        (--organization-id=<org_id>|--organization=<org_name>|--organization-label=<org_label>)

    :expectedresults: Errata is filtered by product and org.
    """
    params = []
    for product in products_with_repos:
        param = {'per-page': PER_PAGE_LARGE}

        if filter_by_org == 'id':
            param['organization-id'] = product.organization.id
        elif filter_by_org == 'name':
            param['organization'] = product.organization.name
        elif filter_by_org == 'label':
            param['organization-label'] = product.organization.label

        if filter_by_product == 'id':
            param['product-id'] = product.id
        elif filter_by_product == 'name':
            param['product'] = product.name

        params.append(param)

    errata_ids = get_errata_ids(*params)
    check_errata(errata_ids)


@pytest.mark.tier3
def test_negative_list_filter_by_product_name(products_with_repos):
    """Attempt to Filter errata by product name

    :id: c7a5988b-668f-4c48-bc1e-97cb968a2563

    :BZ: 1400235

    :Setup: Errata synced on satellite server.

    :Steps: erratum list --product=<product_name>

    :expectedresults: Error must be returned.

    :CaseImportance: Low

    :CaseLevel: System
    """
    with pytest.raises(CLIReturnCodeError):
        Erratum.list({'product': products_with_repos[0].name, 'per-page': PER_PAGE_LARGE})


@pytest.mark.tier3
@pytest.mark.parametrize(
    'filter_by_org', ('id', 'name', 'label'), ids=('org_id', 'org_name', 'org_label')
)
def test_positive_list_filter_by_org(products_with_repos, filter_by_org):
    """Filter errata by org id, name, or label.

    :id: de7646be-7ac8-4dbe-8cc3-6959808d78fa

    :parametrized: yes

    :Setup: Errata synced on satellite server.

    :Steps: erratum list
        (--organization-id=<org_id>|--organization=<org_name>|--organization-label=<org_label>)

    :expectedresults: Errata are filtered by org id, name, or label.
    """
    params = []
    for product in products_with_repos:
        param = {'per-page': PER_PAGE_LARGE}

        if filter_by_org == 'id':
            param['organization-id'] = product.organization.id
        elif filter_by_org == 'name':
            param['organization'] = product.organization.name
        elif filter_by_org == 'label':
            param['organization-label'] = product.organization.label

        params.append(param)

    errata_ids = get_errata_ids(*params)
    check_errata(errata_ids, by_org=True)


@pytest.mark.run_in_one_thread
@pytest.mark.tier3
def test_positive_list_filter_by_cve(module_org, rh_repo):
    """Filter errata by CVE

    :id: 7791137c-95a7-4518-a56b-766a5680c5fb

    :Setup: Errata synced on satellite server.

    :Steps: erratum list --cve <cve_id>

    :expectedresults: Errata is filtered by CVE.

    """
    RepositorySet.enable(
        {
            'name': REPOSET['rhva6'],
            'organization-id': module_org.id,
            'product': PRDS['rhel'],
            'releasever': '6Server',
            'basearch': 'x86_64',
        }
    )
    Repository.synchronize(
        {
            'name': REPOS['rhva6']['name'],
            'organization-id': module_org.id,
            'product': PRDS['rhel'],
        }
    )
    repository_info = Repository.info(
        {
            'name': REPOS['rhva6']['name'],
            'organization-id': module_org.id,
            'product': PRDS['rhel'],
        }
    )

    assert REAL_4_ERRATA_ID in {
        errata['errata-id'] for errata in Erratum.list({'repository-id': repository_info['id']})
    }

    for errata_cve in REAL_4_ERRATA_CVES:
        assert REAL_4_ERRATA_ID in {
            errata['errata-id'] for errata in Erratum.list({'cve': errata_cve})
        }


@pytest.mark.tier3
@pytest.mark.upgrade
def test_positive_user_permission(products_with_repos):
    """Show errata only if the User has permissions to view them

    :id: f350c13b-8cf9-4aa5-8c3a-1c48397ea514

    :Setup:

        1. Create two products with one repo each. Sync them.
        2. Make sure that they both have errata.
        3. Create a user with view access on one product and not on the
           other.

    :Steps: erratum list --organization-id=<orgid>

    :expectedresults: Check that the new user is able to see errata for one
        product only.

    :BZ: 1403947
    """
    user_password = gen_string('alphanumeric')
    user_name = gen_string('alphanumeric')

    product = products_with_repos[3]
    org = product.organization

    # get the available permissions
    permissions = Filter.available_permissions()
    user_required_permissions_names = ['view_products']
    # get the user required permissions ids
    user_required_permissions_ids = [
        permission['id']
        for permission in permissions
        if permission['name'] in user_required_permissions_names
    ]
    assert len(user_required_permissions_ids) > 0

    # create a role
    role = make_role({'organization-ids': org.id})

    # create a filter with the required permissions for role with product
    # one only
    make_filter(
        {
            'permission-ids': user_required_permissions_ids,
            'role-id': role['id'],
            'search': f"name = {product.name}",
        }
    )

    # create a new user and assign him the created role permissions
    user = make_user(
        {
            'admin': False,
            'login': user_name,
            'password': user_password,
            'organization-ids': [org.id],
            'default-organization-id': org.id,
        }
    )
    User.add_role({'id': user['id'], 'role-id': role['id']})

    # make sure the user is not admin and has only the permissions assigned
    user = User.info({'id': user['id']})
    assert user['admin'] == 'no'
    assert set(user['roles']) == {role['name']}

    # try to get organization info
    # get the info as admin user first
    org_info = Org.info({'id': org.id})
    assert str(org.id) == org_info['id']
    assert org.name == org_info['name']

    # get the organization info as the created user
    with pytest.raises(CLIReturnCodeError) as context:
        Org.with_user(user_name, user_password).info({'id': org.id})
    assert 'Missing one of the required permissions: view_organizations' in context.value.stderr

    # try to get the erratum products list by organization id only
    # ensure that all products erratum are accessible by admin user
    admin_org_errata_ids = [
        errata['errata-id'] for errata in Erratum.list({'organization-id': org.id})
    ]
    assert REPOS_WITH_ERRATA[2]['errata_id'] in admin_org_errata_ids
    assert REPOS_WITH_ERRATA[3]['errata_id'] in admin_org_errata_ids

    assert len(admin_org_errata_ids) == (
        REPOS_WITH_ERRATA[2]['errata_count'] + REPOS_WITH_ERRATA[3]['errata_count']
    )

    # ensure that the created user see only the erratum product that was
    # assigned in permissions
    user_org_errata_ids = [
        errata['errata-id']
        for errata in Erratum.with_user(user_name, user_password).list({'organization-id': org.id})
    ]
    assert len(user_org_errata_ids) == REPOS_WITH_ERRATA[3]['errata_count']
    assert REPOS_WITH_ERRATA[3]['errata_id'] in user_org_errata_ids
    assert REPOS_WITH_ERRATA[2]['errata_id'] not in user_org_errata_ids


@pytest.mark.tier3
def test_positive_check_errata_dates(module_org):
    """Check for errata dates in `hammer erratum list`

    :id: b19286ae-bdb4-4319-87d0-5d3ff06c5f38

    :expectedresults: Display errata date when using hammer erratum list

    :CaseImportance: High

    :BZ: 1695163
    """
    product = entities.Product(organization=module_org).create()
    repo = make_repository(
        {'content-type': 'yum', 'product-id': product.id, 'url': REPO_WITH_ERRATA['url']}
    )
    # Synchronize custom repository
    Repository.synchronize({'id': repo['id']})
    result = Erratum.list(options={'per-page': '5', 'fields': 'Issued'})
    assert 'issued' in result[0]

    # Verify any errata ISSUED date from stdout
    validate_issued_date = datetime.strptime(result[0]['issued'], '%Y-%m-%d').date()
    assert isinstance(validate_issued_date, date)

    result = Erratum.list(options={'per-page': '5', 'fields': 'Updated'})
    assert 'updated' in result[0]

    # Verify any errata UPDATED date from stdout
    validate_updated_date = datetime.strptime(result[0]['updated'], '%Y-%m-%d').date()
    assert isinstance(validate_updated_date, date)


@pytest.fixture(scope='module')
def rh_repo_module_manifest(module_manifest_org):
    """Use module manifest org, creates RH tools repo, syncs and returns RH repo."""
    # enable rhel repo and return its ID
    rh_repo_id = enable_rhrepo_and_fetchid(
        basearch=DEFAULT_ARCHITECTURE,
        org_id=module_manifest_org.id,
        product=PRDS['rhel'],
        repo=REPOS['rhst7']['name'],
        reposet=REPOSET['rhst7'],
        releasever=None,
    )
    # Sync step because repo is not synced by default
    rh_repo = entities.Repository(id=rh_repo_id).read()
    rh_repo.sync()
    return rh_repo


"""Section for tests using RHEL7.7 Content Host.
   The applicability tests using Default Content View are related to the introduction of Pulp3.
   """


@pytest.fixture(scope='module')
def default_contentview(module_manifest_org):
    return entities.ContentView(organization=module_manifest_org, name=DEFAULT_CV).search()


@pytest.fixture(scope='module')
def new_module_ak(module_manifest_org, rh_repo_module_manifest, default_lce):
    new_module_ak = entities.ActivationKey(
        content_view=module_manifest_org.default_content_view,
        environment=entities.LifecycleEnvironment(id=module_manifest_org.library.id),
        organization=module_manifest_org,
    ).create()
    # Ensure tools repo is enabled in the activation key
    new_module_ak.content_override(
        data={'content_overrides': [{'content_label': REPOS['rhst7']['id'], 'value': '1'}]}
    )
    # Fetch available subscriptions
    subs = entities.Subscription(organization=module_manifest_org).search(
        query={'search': f'{DEFAULT_SUBSCRIPTION_NAME}'}
    )
    assert subs
    # Add default subscription to activation key
    new_module_ak.add_subscriptions(data={'subscription_id': subs[0].id})
    return new_module_ak


@pytest.fixture
def errata_host(module_manifest_org, rhel77_contenthost_module, new_module_ak):
    """A RHEL77 Content Host that has applicable errata and registered to Library"""
    # python-psutil is obsoleted by python2-psutil, so get older python2-psutil for errata test
    rhel77_contenthost_module.run(f'rpm -Uvh {settings.repos.epel_repo.url}/{PSUTIL_RPM}')
    rhel77_contenthost_module.install_katello_ca()
    rhel77_contenthost_module.register_contenthost(module_manifest_org.label, new_module_ak.name)
    assert rhel77_contenthost_module.nailgun_host.read_json()['subscription_status'] == 0
    rhel77_contenthost_module.install_katello_host_tools()
    return rhel77_contenthost_module


@pytest.fixture
def chost(module_manifest_org, rhel77_contenthost_module, new_module_ak):
    """A RHEL77 Content Host registered to Library that does not have applicable errata"""
    rhel77_contenthost_module.install_katello_ca()
    rhel77_contenthost_module.register_contenthost(module_manifest_org.label, new_module_ak.name)
    assert rhel77_contenthost_module.nailgun_host.read_json()['subscription_status'] == 0
    rhel77_contenthost_module.install_katello_host_tools()
    return rhel77_contenthost_module


@pytest.mark.tier2
def test_apply_errata_using_default_content_view(errata_host):
    """Updating an applicable errata on a host attached to the default content view
     causes the errata to not be applicable.

    :id: 91428c25-932e-4ffe-95bb-b2f700201452

    :steps:
        1. Register a host that already requires errata to org with Library
        2. Ensure at least one errata is applicable on the newly registered host
        3. Update errata on the host
        4. Ensure no errata are applicable

    :expectedresults: errata listed successfully and is installable

    :CaseImportance: High
    """
    # check that package errata is applicable
    erratum = Host.errata_list({'host': errata_host.hostname, 'search': f'id = {REAL_0_ERRATA_ID}'})
    assert len(erratum) == 1
    assert erratum[0]['installable'] == 'true'
    # note time for later wait_for_tasks include 2 mins margin of safety.
    timestamp = (datetime.utcnow() - timedelta(minutes=2)).strftime(TIMESTAMP_FMT)
    # Update errata from Library, i.e. Default CV
    errata_host.run(f'yum -y update --advisory {REAL_0_ERRATA_ID}')
    # Wait for upload profile event (in case Satellite system slow)
    wait_for_tasks(
        search_query=(
            'label = Actions::Katello::Host::UploadProfiles'
            f' and resource_id = {errata_host.nailgun_host.id}'
            f' and started_at >= "{timestamp}"'
        ),
        search_rate=15,
        max_tries=10,
    )
    # Assert that the erratum is no longer applicable
    erratum = Host.errata_list({'host': errata_host.hostname, 'search': f'id = {REAL_0_ERRATA_ID}'})
    assert len(erratum) == 0


@pytest.mark.tier2
def test_update_applicable_package_using_default_content_view(errata_host):
    """Updating an applicable package on a host attached to the default content view causes the
    package to not be applicable or installable.

    :id: f761f39c-026c-4987-8c1e-deec895f09a8

    :setup: Register a host that already requires errata to org with Library

    :steps:
        1. Ensure the expected package is applicable
        2. Update the applicable package on the host
        3. Ensure the package is no longer applicable

    :expectedresults: after updating the package it is no longer shown as applicable

    :CaseImportance: High
    """
    # check that package is applicable
    applicable_packages = Package.list(
        {
            'host-id': errata_host.nailgun_host.id,
            'packages-restrict-applicable': 'true',
            'search': f'name={REAL_RHEL7_0_2_PACKAGE_NAME}',
        }
    )
    assert len(applicable_packages) == 1
    assert REAL_RHEL7_0_2_PACKAGE_NAME in applicable_packages[0]['filename']
    # note time for later wait_for_tasks include 2 mins margin of safety.
    timestamp = (datetime.utcnow() - timedelta(minutes=2)).strftime(TIMESTAMP_FMT)
    # Update package from Library, i.e. Default CV
    errata_host.run(f'yum -y update {REAL_RHEL7_0_2_PACKAGE_NAME}')
    # Wait for upload profile event (in case Satellite system slow)
    wait_for_tasks(
        search_query=(
            'label = Actions::Katello::Host::UploadProfiles'
            f' and resource_id = {errata_host.nailgun_host.id}'
            f' and started_at >= "{timestamp}"'
        ),
        search_rate=15,
        max_tries=10,
    )
    # Assert that the package is no longer applicable
    applicable_packages = Package.list(
        {
            'host-id': errata_host.nailgun_host.id,
            'packages-restrict-applicable': 'true',
            'search': f'name={REAL_RHEL7_0_2_PACKAGE_NAME}',
        }
    )
    assert len(applicable_packages) == 0


@pytest.mark.tier2
def test_downgrade_applicable_package_using_default_content_view(errata_host):
    """Downgrading a package on a host attached to the default content view
    causes the package to become applicable and installable.

    :id: 8503dff8-c2d9-4818-a607-746dc551894b

    :setup: Register a host that already requires errata to org with Library

    :steps:
        1. Update the applicable package
        2. Ensure the expected package is not applicable
        3. Downgrade the applicable package on the host using yum
        4. Ensure the package is now applicable

    :expectedresults: downgraded package shows as applicable

    :CaseImportance: High
    """
    # Update package from Library, i.e. Default CV
    errata_host.run(f'yum -y update {REAL_RHEL7_0_2_PACKAGE_NAME}')
    # Assert that the package is not applicable
    applicable_packages = Package.list(
        {
            'host-id': errata_host.nailgun_host.id,
            'packages-restrict-applicable': 'true',
            'search': f'name={REAL_RHEL7_0_2_PACKAGE_NAME}',
        }
    )
    assert len(applicable_packages) == 0
    # note time for later wait_for_tasks include 2 mins margin of safety.
    timestamp = (datetime.utcnow() - timedelta(minutes=2)).strftime(TIMESTAMP_FMT)
    # Downgrade package (we can't get it from Library, so get older one from EPEL)
    errata_host.run(f'curl -O {settings.repos.epel_repo.url}/{PSUTIL_RPM}')
    errata_host.run(f'yum -y downgrade {PSUTIL_RPM}')
    # Wait for upload profile event (in case Satellite system slow)
    wait_for_tasks(
        search_query=(
            'label = Actions::Katello::Host::UploadProfiles'
            f' and resource_id = {errata_host.nailgun_host.id}'
            f' and started_at >= "{timestamp}"'
        ),
        search_rate=15,
        max_tries=10,
    )
    # check that package is applicable
    applicable_packages = Package.list(
        {
            'host-id': errata_host.nailgun_host.id,
            'packages-restrict-applicable': 'true',
            'search': f'name={REAL_RHEL7_0_2_PACKAGE_NAME}',
        }
    )
    assert len(applicable_packages) == 1
    assert REAL_RHEL7_0_2_PACKAGE_NAME in applicable_packages[0]['filename']


@pytest.mark.tier2
def test_install_applicable_package_to_registerd_host(chost):
    """Installing an older package to an already registered host should show the newer package
    and errata as applicable and installable.

    :id: 519bfe91-cf86-4d6e-94ef-aaf3e5d40a81

    :setup: Register a host to default org with Library

    :steps:
        1. Ensure package is not applicable
        2. Install package that has errata
        3. Ensure the expected package is applicable

    :expectedresults: Installed package shows errata as applicable and installable

    :CaseImportance: High
    """
    # Assert that the package is not applicable
    applicable_packages = Package.list(
        {
            'host-id': chost.nailgun_host.id,
            'packages-restrict-applicable': 'true',
            'search': f'name={REAL_RHEL7_0_2_PACKAGE_NAME}',
        }
    )
    assert len(applicable_packages) == 0
    # note time for later wait_for_tasks include 2 mins margin of safety.
    timestamp = (datetime.utcnow() - timedelta(minutes=2)).strftime(TIMESTAMP_FMT)
    # python-psutil is obsoleted by python2-psutil, so download older python2-psutil for this test
    chost.run(f'curl -O {settings.repos.epel_repo.url}/{PSUTIL_RPM}')
    chost.run(f'yum -y install {PSUTIL_RPM}')
    # Wait for upload profile event (in case Satellite system slow)
    wait_for_tasks(
        search_query=(
            'label = Actions::Katello::Host::UploadProfiles'
            f' and resource_id = {chost.nailgun_host.id}'
            f' and started_at >= "{timestamp}"'
        ),
        search_rate=15,
        max_tries=10,
    )
    # check that package is applicable
    applicable_packages = Package.list(
        {
            'host-id': chost.nailgun_host.id,
            'packages-restrict-applicable': 'true',
            'search': f'name={REAL_RHEL7_0_2_PACKAGE_NAME}',
        }
    )
    assert len(applicable_packages) == 1
    assert REAL_RHEL7_0_2_PACKAGE_NAME in applicable_packages[0]['filename']


@pytest.mark.tier2
def test_downgrading_package_shows_errata_from_library(errata_host, module_manifest_org):
    """Downgrading a package on a host attached to the default content view
    causes the package to become applicable and installable.

    :id: 09cf6325-a003-4eb2-bc98-bc50b2e4e4a0

    :setup: Register a host that already requires errata to org with Library

    :steps:
        1. Update the applicable package
        2. Ensure the expected package is not applicable
        3. Downgrade the applicable package on the host using yum
        4. Ensure the errata is now applicable

    :expectedresults: errata shows as applicable

    :CaseImportance: High
    """
    # Update package from Library, i.e. Default CV
    errata_host.run(f'yum -y update {REAL_RHEL7_0_2_PACKAGE_NAME}')
    # Assert that the package is not applicable
    applicable_packages = Package.list(
        {
            'host-id': errata_host.nailgun_host.id,
            'packages-restrict-applicable': 'true',
            'search': f'name={REAL_RHEL7_0_2_PACKAGE_NAME}',
        }
    )
    assert len(applicable_packages) == 0
    # note time for later wait_for_tasks include 2 mins margin of safety.
    timestamp = (datetime.utcnow() - timedelta(minutes=2)).strftime(TIMESTAMP_FMT)
    # Downgrade package (we can't get it from Library, so get older one from EPEL)
    errata_host.run(f'curl -O {settings.repos.epel_repo.url}/{PSUTIL_RPM}')
    errata_host.run(f'yum -y downgrade {PSUTIL_RPM}')
    # Wait for upload profile event (in case Satellite system slow)
    wait_for_tasks(
        search_query=(
            'label = Actions::Katello::Host::UploadProfiles'
            f' and resource_id = {errata_host.nailgun_host.id}'
            f' and started_at >= "{timestamp}"'
        ),
        search_rate=15,
        max_tries=10,
    )
    # check that errata is applicable
    param = {
        'errata-restrict-applicable': 1,
        'organization-id': module_manifest_org.id,
        'per-page': PER_PAGE_LARGE,
    }
    errata_ids = get_errata_ids(param)
    assert REAL_0_ERRATA_ID in errata_ids
