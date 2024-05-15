"""CLI Tests for the errata management feature

:Requirement: Errata

:CaseAutomation: Automated

:CaseComponent: ErrataManagement

:team: Phoenix-content

:CaseImportance: High
"""

from datetime import date, datetime, timedelta
from operator import itemgetter
import re

from broker import Broker
import pytest

from robottelo.config import settings
from robottelo.constants import (
    DEFAULT_ARCHITECTURE,
    FAKE_1_CUSTOM_PACKAGE,
    FAKE_2_CUSTOM_PACKAGE,
    FAKE_2_CUSTOM_PACKAGE_NAME,
    FAKE_4_CUSTOM_PACKAGE,
    FAKE_4_CUSTOM_PACKAGE_NAME,
    FAKE_5_CUSTOM_PACKAGE,
    PRDS,
    REAL_4_ERRATA_CVES,
    REAL_4_ERRATA_ID,
    REPOS,
    REPOSET,
)
from robottelo.exceptions import CLIReturnCodeError
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
TIMESTAMP_FMT_S = '%Y-%m-%d %H:%M:%S'

PSUTIL_RPM = 'python2-psutil-5.6.7-1.el7.x86_64.rpm'

pytestmark = [
    pytest.mark.skipif(
        (not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url'
    ),
    pytest.mark.run_in_one_thread,
]


@pytest.fixture(scope='module')
def orgs(module_target_sat):
    """Create and return a list of three orgs."""
    return [module_target_sat.api.Organization().create() for _ in range(3)]


@pytest.fixture(scope='module')
def products_with_repos(orgs, module_target_sat):
    """Create and return a list of products. For each product, create and sync a single repo."""
    products = []
    # Create one product for each org, and a second product for the last org.
    for org, params in zip(orgs + orgs[-1:], REPOS_WITH_ERRATA, strict=True):
        product = module_target_sat.api.Product(organization=org).create()
        # Replace the organization entity returned by create(), which contains only the id,
        # with the one we already have.
        product.organization = org
        products.append(product)
        repo = module_target_sat.cli_factory.make_repository(
            {
                'download-policy': 'immediate',
                'organization-id': product.organization.id,
                'product-id': product.id,
                'url': params['url'],
            }
        )
        module_target_sat.cli.Repository.synchronize({'id': repo.id})

    return products


@pytest.fixture(scope='module')
def custom_repo(
    module_sca_manifest_org, module_lce, module_cv, module_ak_cv_lce, module_target_sat
):
    """Create custom repo and add a subscription to activation key."""
    module_target_sat.cli_factory.setup_org_for_a_custom_repo(
        {
            'url': REPO_WITH_ERRATA['url'],
            'organization-id': module_sca_manifest_org.id,
            'content-view-id': module_cv.id,
            'lifecycle-environment-id': module_lce.id,
            'activationkey-id': module_ak_cv_lce.id,
        }
    )


@pytest.fixture(scope='module')
def rh_repo_module_manifest(module_sca_manifest_org, module_target_sat):
    """Use module manifest org, creates RH clients repo, syncs and returns RH repo."""
    # enable rhel repo and return its ID
    rh_repo_id = module_target_sat.api_factory.enable_rhrepo_and_fetchid(
        basearch=DEFAULT_ARCHITECTURE,
        org_id=module_sca_manifest_org.id,
        product=PRDS['rhel8'],
        repo=REPOS['rhsclient8']['name'],
        reposet=REPOSET['rhsclient8'],
        releasever=None,
    )
    # Sync step because repo is not synced by default
    rh_repo = module_target_sat.api.Repository(id=rh_repo_id).read()
    rh_repo.sync()
    return rh_repo


@pytest.fixture(scope='module')
def hosts(request):
    """Deploy hosts via broker."""
    num_hosts = getattr(request, 'param', 2)
    with Broker(nick='rhel8', host_class=ContentHost, _count=num_hosts) as hosts:
        if not isinstance(hosts, list) or len(hosts) != num_hosts:
            pytest.fail('Failed to provision the expected number of hosts.')
        yield hosts


@pytest.fixture(scope='module')
def register_hosts(
    hosts,
    module_sca_manifest_org,
    module_lce,
    module_ak,
    module_target_sat,
):
    """Register hosts to Satellite"""
    for host in hosts:
        module_target_sat.cli_factory.setup_org_for_a_custom_repo(
            {
                'url': REPO_WITH_ERRATA['url'],
                'organization-id': module_sca_manifest_org.id,
                'lifecycle-environment-id': module_lce.id,
                'activationkey-id': module_ak.id,
            }
        )
        host.register(
            activation_keys=module_ak.name,
            target=module_target_sat,
            org=module_sca_manifest_org,
            loc=None,
        )
        assert host.subscribed

    return hosts


@pytest.fixture
def errata_hosts(register_hosts, target_sat):
    """Ensure that rpm is installed on host."""
    for host in register_hosts:
        # Enable all custom and rh repositories.
        host.execute(r'subscription-manager repos --enable \*')
        host.execute(r'yum-config-manager --enable \*')
        host.add_rex_key(satellite=target_sat)
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
def host_collection(module_sca_manifest_org, module_ak_cv_lce, register_hosts, module_target_sat):
    """Create and setup host collection."""
    host_collection = module_target_sat.cli_factory.make_host_collection(
        {'organization-id': module_sca_manifest_org.id}
    )
    host_ids = [
        module_target_sat.cli.Host.info({'name': host.hostname})['id'] for host in register_hosts
    ]
    module_target_sat.cli.HostCollection.add_host(
        {
            'id': host_collection['id'],
            'organization-id': module_sca_manifest_org.id,
            'host-ids': host_ids,
        }
    )
    module_target_sat.cli.ActivationKey.add_host_collection(
        {
            'id': module_ak_cv_lce.id,
            'host-collection-id': host_collection['id'],
            'organization-id': module_sca_manifest_org.id,
        }
    )
    return host_collection


def start_and_wait_errata_recalculate(sat, host):
    """Helper to find any in-progress errata applicability task and wait_for completion.
    Otherwise, schedule errata recalculation, wait for the task.
    Find the successful completed task(s).

    :param sat: Satellite instance to check for task(s)
    :param host: ContentHost instance to schedule errata recalculate
    """
    # Find any in-progress task for this host
    search = "label = Actions::Katello::Applicability::Hosts::BulkGenerate and result = pending"
    applicability_task_running = sat.cli.Task.list_tasks({'search': search})
    # No task in progress, invoke errata recalculate
    if len(applicability_task_running) == 0:
        sat.cli.Host.errata_recalculate({'host-id': host.nailgun_host.id})
        host.run('subscription-manager repos')
    # Note time check for later wait_for_tasks include 30s margin of safety
    timestamp = (datetime.utcnow() - timedelta(seconds=30)).strftime(TIMESTAMP_FMT_S)
    # Wait for upload profile event (in case Satellite system is slow)
    sat.wait_for_tasks(
        search_query=(
            'label = Actions::Katello::Applicability::Hosts::BulkGenerate'
            f' and started_at >= "{timestamp}"'
        ),
        search_rate=15,
        max_tries=10,
    )
    # Find the successful finished task(s)
    search = (
        "label = Actions::Katello::Applicability::Hosts::BulkGenerate"
        " and result = success"
        f" and started_at >= '{timestamp}'"
    )
    applicability_task_success = sat.cli.Task.list_tasks({'search': search})
    assert applicability_task_success, f'No successful task found by search: {search}'


def is_rpm_installed(host, rpm=None):
    """Return whether the specified rpm is installed.

    :type host: robottelo.hosts.ContentHost instance
    :type rpm: str
    :rtype: bool
    """
    rpm = rpm or REPO_WITH_ERRATA['errata'][0]['new_package']
    return not host.execute(f'rpm -q {rpm}').status


def get_sorted_errata_info_by_id(sat, errata_ids, sort_by='issued', sort_reversed=False):
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
        sat.cli.Erratum.info(options={'id': errata_id}, output_format='json')
        for errata_id in errata_ids
    ]
    return sorted(errata_info, key=itemgetter(sort_by), reverse=sort_reversed)


def get_errata_ids(sat, *params):
    """Return list of sets of errata ids corresponding to the provided params."""
    errata_ids = [
        {errata['errata-id'] for errata in sat.cli.Erratum.list(param)} for param in params
    ]
    return errata_ids[0] if len(errata_ids) == 1 else errata_ids


def check_errata(errata_ids, by_org=False):
    """Verify that each list of errata ids matches the expected values

    :param errata_ids: a list containing a list of errata ids for each repo
    :type errata_ids: list[list]
    """
    for ids, repo_with_errata in zip(errata_ids, REPOS_WITH_ERRATA, strict=True):
        assert len(ids) == repo_with_errata['org_errata_count' if by_org else 'errata_count']
        assert repo_with_errata['errata_id'] in ids


def filter_sort_errata(sat, org, sort_by_date='issued', filter_by_org=None):
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

        sort_reversed = sort_order == 'DESC'

        errata_list = sat.cli.Erratum.list(list_param)
        assert len(errata_list) > 0

        # Build a sorted errata info list, which also contains the sort field.
        errata_internal_ids = [errata['id'] for errata in errata_list]
        sorted_errata_info = get_sorted_errata_info_by_id(
            sat, errata_internal_ids, sort_by=sort_by_date, sort_reversed=sort_reversed
        )

        sort_field_values = [errata[sort_by_date] for errata in sorted_errata_info]
        assert sort_field_values == sorted(sort_field_values, reverse=sort_reversed)

        errata_ids = [errata['errata-id'] for errata in errata_list]
        sorted_errata_ids = [errata['errata-id'] for errata in sorted_errata_info]
        assert errata_ids == sorted_errata_ids


def cv_publish_promote(sat, cv, org, lce, force=False):
    """Publish and promote a new version into the given lifecycle environment.

    :param cv: content view
    :type cv: entities.ContentView
    :param org: organization
    :type org: entities.Organization
    :param lce: lifecycle environment
    :type lce: entities.LifecycleEnvironment
    """
    sat.cli.ContentView.publish({'id': cv.id, 'organization': org})
    # Sort CV Version results by --id, grab last version (latest)
    cvv_id = sorted(cvv['id'] for cvv in sat.cli.ContentView.info({'id': cv.id})['versions'])[-1]
    sat.cli.ContentView.version_promote(
        {
            'id': cvv_id,
            'organization': org,
            'to-lifecycle-environment-id': lce.id,
            'force': force,
        }
    )


def cv_filter_cleanup(sat, filter_id, cv, org, lce):
    """Delete the cv filter, then publish and promote an unfiltered version."""
    sat.cli.ContentViewFilter.delete(
        {
            'content-view-id': cv.id,
            'id': filter_id,
            'organization-id': org.id,
        }
    )
    cv = cv.read()
    cv_publish_promote(sat, cv, org, lce)


@pytest.mark.tier3
@pytest.mark.parametrize('filter_by_hc', ['id', 'name'], ids=('hc_id', 'hc_name'))
@pytest.mark.parametrize(
    'filter_by_org', ['id', 'name', 'title'], ids=('org_id', 'org_name', 'org_title')
)
@pytest.mark.no_containers
def test_positive_install_by_host_collection_and_org(
    module_sca_manifest_org,
    host_collection,
    errata_hosts,
    filter_by_hc,
    filter_by_org,
    target_sat,
):
    """Use host collection id or name and org id, name, or label to install an update on the host
    collection.

    :id: 1b063f76-c85f-42fb-a919-5de319b09b99

    :parametrized: yes

    :customerscenario: true

    :Setup: Errata synced on satellite server.

    :Steps: Use Job Invocation to install errata
        job-invocation create --feature="katello_errata_install" \
        --search-query="host_collection[-id] = <value>" --inputs="errata=<errata_id>" \
        --organization[-id][-title]=<value>'

    :expectedresults: Erratum is installed.

    :BZ: 1457977, 1983043
    """
    errata_id = REPO_WITH_ERRATA['errata'][0]['id']

    if filter_by_hc == 'id':
        host_collection_query = f'host_collection_id = {host_collection["id"]}'
    elif filter_by_hc == 'name':
        host_collection_query = f'host_collection = {host_collection["name"]}'

    if filter_by_org == "id":
        organization_key = 'organization-id'
        organization_value = module_sca_manifest_org.id
    elif filter_by_org == "name":
        organization_key = 'organization'
        organization_value = module_sca_manifest_org.name
    elif filter_by_org == "title":
        organization_key = 'organization-title'
        organization_value = module_sca_manifest_org.title

    target_sat.cli.JobInvocation.create(
        {
            'feature': 'katello_errata_install',
            'search-query': host_collection_query,
            'inputs': f"errata='{errata_id}'",
            f'{organization_key}': f'{organization_value}',
        }
    )

    for host in errata_hosts:
        assert is_rpm_installed(host)


@pytest.mark.tier3
def test_negative_install_erratum_on_host_collection(
    module_sca_manifest_org, host_collection, module_target_sat
):
    """Attempt to install an erratum on a host collection
        This functionality was removed with katello-agent

    :id: 753d36f0-d19b-494d-a247-ce2d61c4cf74

    :Setup: Errata synced on satellite server.

    :Steps: host-collection erratum install --errata <errata>
        --organization-id <org_id>

    :expectedresults: Error message thrown. Not supported. Use the remote execution equivalent

    :CaseImportance: Low
    """
    module_target_sat.cli_factory.make_host_collection(
        {'organization-id': module_sca_manifest_org.id}
    )
    with pytest.raises(CLIReturnCodeError) as error:
        module_target_sat.cli.HostCollection.erratum_install(
            {
                'organization-id': module_sca_manifest_org.id,
                'errata': [REPO_WITH_ERRATA['errata'][0]['id']],
            }
        )
    assert 'Not supported. Use the remote execution equivalent' in error.value.stderr


@pytest.mark.tier3
@pytest.mark.upgrade
def test_positive_list_affected_chosts(module_sca_manifest_org, errata_hosts, target_sat):
    """View a list of affected content hosts for an erratum.

    :id: 3b592253-52c0-4165-9a48-ba55287e9ee9

    :Setup: Errata synced on satellite server, custom package installed on errata hosts.

    :Steps: host list --search 'applicable_errata = <erratum_id>'
        --organization-id=<org_id>

    :expectedresults: List of affected content hosts for an erratum is
        displayed.

    :CaseAutomation: Automated
    """
    result = target_sat.cli.Host.list(
        {
            'search': f'applicable_errata = {REPO_WITH_ERRATA["errata"][0]["id"]}',
            'organization-id': module_sca_manifest_org.id,
            'fields': 'Name',
        }
    )
    reported_hostnames = {item['name'] for item in result}
    hostnames = {host.hostname for host in errata_hosts}
    assert hostnames.issubset(
        reported_hostnames
    ), 'One or more hostnames not found in list of applicable hosts'


@pytest.mark.tier3
@pytest.mark.no_containers
def test_install_errata_to_one_host(
    module_sca_manifest_org, errata_hosts, host_collection, target_sat
):
    """Install an erratum to one of the hosts in a host collection.

    :id: bfcee2de-3448-497e-a696-fcd30cea9d33

    :expectedresults: Errata was successfully installed in only one of the hosts in
        the host collection

    :Setup: Errata synced on satellite server, custom package installed on errata hosts.

    :customerscenario: true

    :Steps:
        1. Remove packages from one host.
        2. Recalculate errata for both hosts.
        3. Assert first host does not have the package.
        4. Assert second host does have the new package.


    :expectedresults: Erratum is only installed on one host.

    :BZ: 1810774
    """
    errata = REPO_WITH_ERRATA['errata'][0]

    # Remove the package on first host to remove need for errata.
    result = errata_hosts[0].execute(f'yum erase -y {errata["package_name"]}')
    assert result.status == 0, f'Failed to erase the rpm: {result.stdout}'

    for host in errata_hosts:
        start_and_wait_errata_recalculate(target_sat, host)

    assert not is_rpm_installed(
        errata_hosts[0], rpm=errata['package_name']
    ), 'Package should not be installed on host.'
    assert is_rpm_installed(
        errata_hosts[1], rpm=errata['package_name']
    ), 'Package should be installed on host.'


@pytest.mark.tier3
@pytest.mark.e2e
def test_positive_list_affected_chosts_by_erratum_restrict_flag(
    target_sat,
    request,
    module_sca_manifest_org,
    module_cv,
    module_lce,
    errata_hosts,
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
        start_and_wait_errata_recalculate(target_sat, host)

    # Create list of uninstallable errata.
    errata = REPO_WITH_ERRATA['errata'][0]
    uninstallable = REPO_WITH_ERRATA['errata_ids'].copy()
    uninstallable.remove(errata['id'])
    # Check search for only installable errata
    param = {
        'errata-restrict-installable': 1,
        'lifecycle-environment-id': module_lce.id,
        'organization-id': module_sca_manifest_org.id,
        'per-page': PER_PAGE_LARGE,
    }
    errata_ids = get_errata_ids(target_sat, param)
    assert errata_ids, 'No installable errata found'
    assert errata['id'] in errata_ids, 'Errata not found in list of installable errata'
    assert not set(uninstallable) & set(errata_ids), 'Unexpected errata found'

    # Check search of errata is not affected by installable=0 restrict flag
    param = {
        'errata-restrict-installable': 0,
        'lifecycle-environment-id': module_lce.id,
        'organization-id': module_sca_manifest_org.id,
        'per-page': PER_PAGE_LARGE,
    }
    errata_ids = get_errata_ids(target_sat, param)
    assert set(REPO_WITH_ERRATA['errata_ids']).issubset(
        errata_ids
    ), 'Errata not found in list of installable errata'

    # Check list of applicable errata
    param = {
        'errata-restrict-applicable': 1,
        'organization-id': module_sca_manifest_org.id,
        'per-page': PER_PAGE_LARGE,
    }
    errata_ids = get_errata_ids(target_sat, param)
    assert errata['id'] in errata_ids, 'Errata not found in list of applicable errata'

    # Check search of errata is not affected by applicable=0 restrict flag
    param = {
        'errata-restrict-applicable': 0,
        'organization-id': module_sca_manifest_org.id,
        'per-page': PER_PAGE_LARGE,
    }
    errata_ids = get_errata_ids(target_sat, param)
    assert set(REPO_WITH_ERRATA['errata_ids']).issubset(
        errata_ids
    ), 'Errata not found in list of applicable errata'

    # Apply a filter and rule to the CV to hide the RPM, thus making erratum not installable
    # Make RPM exclude filter
    cv_filter = target_sat.cli_factory.make_content_view_filter(
        {
            'content-view-id': module_cv.id,
            'name': 'erratum_restrict_test',
            'description': 'Hide the installable errata',
            'organization-id': module_sca_manifest_org.id,
            'type': 'rpm',
            'inclusion': 'false',
        }
    )
    request.addfinalizer(
        lambda: cv_filter_cleanup(
            target_sat, cv_filter['filter-id'], module_cv, module_sca_manifest_org, module_lce
        )
    )

    # Make rule to hide the RPM that creates the need for the installable erratum
    target_sat.cli_factory.content_view_filter_rule(
        {
            'content-view-id': module_cv.id,
            'content-view-filter-id': cv_filter['filter-id'],
            'name': errata['package_name'],
        }
    )

    # Publish and promote a new version with the filter
    cv_publish_promote(target_sat, module_cv, module_sca_manifest_org, module_lce)

    # Check that the installable erratum is no longer present in the list
    param = {
        'errata-restrict-installable': 0,
        'content-view-id': module_cv.id,
        'lifecycle-environment-id': module_lce.id,
        'organization-id': module_sca_manifest_org.id,
        'per-page': PER_PAGE_LARGE,
    }
    errata_ids = get_errata_ids(target_sat, param)
    assert errata['id'] not in errata_ids, 'Errata not found in list of installable errata'

    # Check errata still applicable
    param = {
        'errata-restrict-applicable': 1,
        'organization-id': module_sca_manifest_org.id,
        'per-page': PER_PAGE_LARGE,
    }
    errata_ids = get_errata_ids(target_sat, param)
    assert errata['id'] in errata_ids, 'Errata not found in list of applicable errata'


@pytest.mark.tier3
def test_host_errata_search_commands(
    request,
    module_sca_manifest_org,
    module_cv,
    module_lce,
    errata_hosts,
    target_sat,
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

    :CaseImportance: Medium

    :expectedresults: The hosts are correctly listed for security and bugfix advisories.
    """

    errata = REPO_WITH_ERRATA['errata']
    # Update package on first host so that the security advisory doesn't apply.
    result = errata_hosts[0].execute(f'yum update -y {errata[0]["new_package"]}')
    assert result.status == 0, 'Failed to install rpm'

    # Update package on second host so that the bugfix advisory doesn't apply.
    result = errata_hosts[1].execute(f'yum update -y {errata[1]["new_package"]}')
    assert result.status == 0, 'Failed to install rpm'

    for host in errata_hosts:
        start_and_wait_errata_recalculate(target_sat, host)

    # Step 1: Search for hosts that require bugfix advisories
    result = target_sat.cli.Host.list(
        {
            'search': 'errata_status = errata_needed',
            'organization-id': module_sca_manifest_org.id,
            'per-page': PER_PAGE_LARGE,
        }
    )
    result = [item['name'] for item in result]
    assert errata_hosts[0].hostname in result
    assert errata_hosts[1].hostname not in result

    # Step 2: Search for hosts that require security advisories
    result = target_sat.cli.Host.list(
        {
            'search': 'errata_status = security_needed',
            'organization-id': module_sca_manifest_org.id,
            'per-page': PER_PAGE_LARGE,
        }
    )
    result = [item['name'] for item in result]
    assert errata_hosts[0].hostname not in result
    assert errata_hosts[1].hostname in result

    # Step 3: Search for hosts that require the specified bugfix advisory
    result = target_sat.cli.Host.list(
        {
            'search': f'applicable_errata = {errata[1]["id"]}',
            'organization-id': module_sca_manifest_org.id,
            'per-page': PER_PAGE_LARGE,
        }
    )
    result = [item['name'] for item in result]
    assert errata_hosts[0].hostname in result
    assert errata_hosts[1].hostname not in result

    # Step 4: Search for hosts that require the specified security advisory
    result = target_sat.cli.Host.list(
        {
            'search': f'applicable_errata = {errata[0]["id"]}',
            'organization-id': module_sca_manifest_org.id,
            'per-page': PER_PAGE_LARGE,
        }
    )
    result = [item['name'] for item in result]
    assert errata_hosts[0].hostname not in result
    assert errata_hosts[1].hostname in result

    # Step 5: Search for hosts that require the specified bugfix package
    result = target_sat.cli.Host.list(
        {
            'search': f'applicable_rpms = {errata[1]["new_package"]}',
            'organization-id': module_sca_manifest_org.id,
            'per-page': PER_PAGE_LARGE,
        }
    )
    result = [item['name'] for item in result]
    assert errata_hosts[0].hostname in result
    assert errata_hosts[1].hostname not in result

    # Step 6: Search for hosts that require the specified security package
    result = target_sat.cli.Host.list(
        {
            'search': f'applicable_rpms = {errata[0]["new_package"]}',
            'organization-id': module_sca_manifest_org.id,
            'per-page': PER_PAGE_LARGE,
        }
    )
    result = [item['name'] for item in result]
    assert errata_hosts[0].hostname not in result
    assert errata_hosts[1].hostname in result

    # Step 7: Apply filter and rule to CV to hide RPM, thus making erratum not installable
    # Make RPM exclude filter
    cv_filter = target_sat.cli_factory.make_content_view_filter(
        {
            'content-view-id': module_cv.id,
            'name': 'erratum_search_test',
            'description': 'Hide the installable errata',
            'organization-id': module_sca_manifest_org.id,
            'type': 'rpm',
            'inclusion': 'false',
        }
    )
    request.addfinalizer(
        lambda: cv_filter_cleanup(
            target_sat, cv_filter['filter-id'], module_cv, module_sca_manifest_org, module_lce
        )
    )
    # Make rule to exclude the specified bugfix package
    target_sat.cli_factory.content_view_filter_rule(
        {
            'content-view-id': module_cv.id,
            'content-view-filter-id': cv_filter['filter-id'],
            'name': errata[1]['package_name'],
        }
    )

    # Publish and promote a new version with the filter
    cv_publish_promote(target_sat, module_cv, module_sca_manifest_org, module_lce)

    # Step 8: Run tests again. Applicable should still be true, installable should now be false.
    # Search for hosts that require the bugfix package.
    result = target_sat.cli.Host.list(
        {
            'search': f'applicable_rpms = {errata[1]["new_package"]}',
            'organization-id': module_sca_manifest_org.id,
            'per-page': PER_PAGE_LARGE,
        }
    )
    result = [item['name'] for item in result]
    assert errata_hosts[0].hostname in result
    assert errata_hosts[1].hostname not in result

    # Search for hosts that require the specified bugfix advisory.
    result = target_sat.cli.Host.list(
        {
            'search': f'installable_errata = {errata[1]["id"]}',
            'organization-id': module_sca_manifest_org.id,
            'per-page': PER_PAGE_LARGE,
        }
    )
    result = [item['name'] for item in result]
    assert errata_hosts[0].hostname in result
    assert errata_hosts[1].hostname not in result


@pytest.mark.tier3
@pytest.mark.parametrize('sort_by_date', ['issued', 'updated'], ids=('issued_date', 'updated_date'))
@pytest.mark.parametrize(
    'filter_by_org',
    ['id', 'name', 'label', None],
    ids=('org_id', 'org_name', 'org_label', 'no_org_filter'),
)
def test_positive_list_filter_by_org_sort_by_date(
    module_sca_manifest_org,
    rh_repo_module_manifest,
    custom_repo,
    filter_by_org,
    sort_by_date,
    module_target_sat,
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
    filter_sort_errata(
        sat=module_target_sat,
        org=module_sca_manifest_org,
        sort_by_date=sort_by_date,
        filter_by_org=filter_by_org,
    )


@pytest.mark.tier3
def test_positive_list_filter_by_product_id(target_sat, products_with_repos):
    """Filter errata by product id

    :id: 7d06950a-c058-48b3-a384-c3565cbd643f

    :Setup: Errata synced on satellite server.

    :Steps: erratum list --product-id=<productid>

    :expectedresults: Errata is filtered by product id.
    """
    params = [
        {'product-id': product.id, 'per-page': PER_PAGE_LARGE} for product in products_with_repos
    ]
    errata_ids = get_errata_ids(target_sat, *params)
    check_errata(errata_ids)


@pytest.mark.tier3
@pytest.mark.parametrize('filter_by_product', ['id', 'name'], ids=('product_id', 'product_name'))
@pytest.mark.parametrize(
    'filter_by_org', ['id', 'name', 'label'], ids=('org_id', 'org_name', 'org_label')
)
def test_positive_list_filter_by_product_and_org(
    target_sat, products_with_repos, filter_by_product, filter_by_org
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

    errata_ids = get_errata_ids(target_sat, *params)
    check_errata(errata_ids)


@pytest.mark.tier3
def test_negative_list_filter_by_product_name(products_with_repos, module_target_sat):
    """Attempt to Filter errata by product name

    :id: c7a5988b-668f-4c48-bc1e-97cb968a2563

    :BZ: 1400235

    :Setup: Errata synced on satellite server.

    :Steps: erratum list --product=<product_name>

    :expectedresults: Error must be returned.

    :CaseImportance: Low
    """
    with pytest.raises(CLIReturnCodeError):
        module_target_sat.cli.Erratum.list(
            {'product': products_with_repos[0].name, 'per-page': PER_PAGE_LARGE}
        )


@pytest.mark.tier3
@pytest.mark.parametrize(
    'filter_by_org', ['id', 'name', 'label'], ids=('org_id', 'org_name', 'org_label')
)
def test_positive_list_filter_by_org(target_sat, products_with_repos, filter_by_org):
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

    errata_ids = get_errata_ids(target_sat, *params)
    check_errata(errata_ids, by_org=True)


@pytest.mark.run_in_one_thread
@pytest.mark.tier3
def test_positive_list_filter_by_cve(module_sca_manifest_org, rh_repo_module_manifest, target_sat):
    """Filter errata by CVE

    :id: 7791137c-95a7-4518-a56b-766a5680c5fb

    :Setup: Errata synced on satellite server.

    :Steps: erratum list --cve <cve_id>

    :expectedresults: Errata is filtered by CVE.
    """
    target_sat.cli.RepositorySet.enable(
        {
            'name': REPOSET['rhva6'],
            'organization-id': module_sca_manifest_org.id,
            'product': PRDS['rhel'],
            'releasever': '6Server',
            'basearch': 'x86_64',
        }
    )
    target_sat.cli.Repository.synchronize(
        {
            'name': REPOS['rhva6']['name'],
            'organization-id': module_sca_manifest_org.id,
            'product': PRDS['rhel'],
        }
    )
    repository_info = target_sat.cli.Repository.info(
        {
            'name': REPOS['rhva6']['name'],
            'organization-id': module_sca_manifest_org.id,
            'product': PRDS['rhel'],
        }
    )

    assert REAL_4_ERRATA_ID in {
        errata['errata-id']
        for errata in target_sat.cli.Erratum.list({'repository-id': repository_info['id']})
    }

    for errata_cve in REAL_4_ERRATA_CVES:
        assert REAL_4_ERRATA_ID in {
            errata['errata-id'] for errata in target_sat.cli.Erratum.list({'cve': errata_cve})
        }


@pytest.mark.tier3
def test_positive_check_errata_dates(module_sca_manifest_org, module_target_sat):
    """Check for errata dates in `hammer erratum list`

    :id: b19286ae-bdb4-4319-87d0-5d3ff06c5f38

    :expectedresults: Display errata date when using hammer erratum list

    :customerscenario: true

    :CaseImportance: High

    :BZ: 1695163
    """
    product = module_target_sat.api.Product(organization=module_sca_manifest_org).create()
    repo = module_target_sat.cli_factory.make_repository(
        {'content-type': 'yum', 'product-id': product.id, 'url': REPO_WITH_ERRATA['url']}
    )
    # Synchronize custom repository
    module_target_sat.cli.Repository.synchronize({'id': repo.id})
    result = module_target_sat.cli.Erratum.list(
        options={'per-page': '5', 'fields': 'Issued'}
    ).split()
    assert 'Issued' in result[0]

    # Verify any errata ISSUED date from stdout
    validate_issued_dates = [datetime.strptime(_date, '%Y-%m-%d').date() for _date in result[1:]]
    assert isinstance(validate_issued_dates, list)
    # make sure there are errata entries
    assert len(validate_issued_dates) > 1
    assert all(isinstance(_issued, date) for _issued in validate_issued_dates)

    result = module_target_sat.cli.Erratum.list(
        options={'per-page': '5', 'fields': 'Updated'}
    ).split()
    assert 'Updated' in result[0]

    # Verify any errata UPDATED date from stdout
    validate_updated_dates = [datetime.strptime(_date, '%Y-%m-%d').date() for _date in result[1:]]
    assert isinstance(validate_updated_dates, list)
    assert len(validate_updated_dates) > 1
    assert all(isinstance(_updated, date) for _updated in validate_updated_dates)


"""Section for tests using RHEL Content Host.
   The applicability tests using Default Content View are related to the introduction of Pulp3.
   """


@pytest.fixture(scope='module')
def new_module_ak(
    module_sca_manifest_org, rh_repo_module_manifest, module_lce_library, module_target_sat
):
    new_module_ak = module_target_sat.api.ActivationKey(
        environment=module_lce_library,
        organization=module_sca_manifest_org,
    ).create()
    # Ensure tools repo is enabled in the activation key
    new_module_ak.content_override(
        data={'content_overrides': [{'content_label': REPOS['rhsclient8']['id'], 'value': '1'}]}
    )
    return new_module_ak.read()


@pytest.fixture
def errata_host(
    target_sat,
    rhel_contenthost,
    module_sca_manifest_org,
    module_lce_library,
    new_module_ak,
):
    """A RHEL Content Host that has applicable errata and registered to Library, using Global Registration.

    To use specific RHEL version(s), parameterize any test importing this fixture like so:
        @pytest.mark.rhel_ver_match('[7, 8, ...]')
    """
    org = module_sca_manifest_org
    cv = target_sat.api.ContentView(
        organization=org,
        environment=[module_lce_library.id],
    ).create()
    target_sat.cli_factory.setup_org_for_a_custom_repo(
        {
            'url': REPO_WITH_ERRATA['url'],
            'organization-id': org.id,
            'lifecycle-environment-id': module_lce_library.id,
            'activationkey-id': new_module_ak.id,
            'content-view-id': cv.id,
        }
    )
    rhel_contenthost.register(
        activation_keys=new_module_ak.name,
        target=target_sat,
        org=org,
        loc=None,
    )
    assert rhel_contenthost.subscribed
    assert rhel_contenthost.applicable_errata_count == 0

    rhel_contenthost.execute(r'yum-config-manager --enable \*')
    rhel_contenthost.execute(r'subscription-manager repos --enable \*')
    for errata in REPO_WITH_ERRATA['errata']:
        # Remove package if present, old or new.
        package_name = errata['package_name']
        result = rhel_contenthost.execute(f'yum erase -y {package_name}')
        if result.status != 0:
            pytest.fail(f'Failed to remove {package_name}: {result.stdout} {result.stderr}')

        # Install old package, so that errata apply.
        old_package = errata['old_package']
        result = rhel_contenthost.execute(f'yum install -y {old_package}')
        if result.status != 0:
            pytest.fail(f'Failed to install {old_package}: {result.stdout} {result.stderr}')

    start_and_wait_errata_recalculate(target_sat, rhel_contenthost)
    assert rhel_contenthost.applicable_errata_count == 2
    return rhel_contenthost


@pytest.mark.tier2
@pytest.mark.no_containers
@pytest.mark.rhel_ver_match('8')
def test_apply_errata_using_default_content_view(errata_host, module_sca_manifest_org, target_sat):
    """Updating an applicable errata on a host attached to the default content view
     causes the errata to not be applicable.

    :id: 91428c25-932e-4ffe-95bb-b2f700201452

    :steps:
        1. Register a host that already requires errata to org with Library
        2. Ensure at least one errata is applicable on the newly registered host
        3. Update errata on the host
        4. Ensure no errata are applicable

    :expectedresults: errata listed successfully and is installable

    :parametrized: yes

    :CaseImportance: High
    """
    assert errata_host.applicable_errata_count > 0
    # Check that package errata is applicable
    erratum_id = REPO_WITH_ERRATA['errata'][0]['id']
    erratum = target_sat.cli.Host.errata_list(
        {'host': errata_host.hostname, 'search': f'id = {erratum_id}'}
    )
    assert len(erratum) == 1
    assert erratum[0]['installable'] == 'true'
    # Update errata from Library, i.e. Default CV
    _job_invoc = target_sat.cli.JobInvocation.create(
        {
            'feature': 'katello_errata_install',
            'search-query': f'name = {errata_host.hostname}',
            'inputs': f'errata={erratum[0]["erratum-id"]}',
            'organization-id': module_sca_manifest_org.id,
        }
    )
    # job invocation started, check status
    assert 'created' in _job_invoc[0]['message']
    assert (_id := _job_invoc[0]['id'])
    assert target_sat.cli.JobInvocation().info(options={'id': _id})['status'] == 'succeeded'
    start_and_wait_errata_recalculate(target_sat, errata_host)

    # Assert that the erratum is no longer applicable
    erratum = target_sat.cli.Host.errata_list(
        {'host': errata_host.hostname, 'search': f'id = {erratum_id}'}
    )
    assert len(erratum) == 0


@pytest.mark.tier2
@pytest.mark.no_containers
@pytest.mark.rhel_ver_match('8')
def test_update_applicable_package_using_default_content_view(errata_host, target_sat):
    """Updating an applicable package on a host attached to the default content view causes the
    package to not be applicable or installable.

    :id: f761f39c-026c-4987-8c1e-deec895f09a8

    :setup: Register a host that already requires errata to org with Library

    :steps:
        1. Ensure the expected package is applicable
        2. Update the applicable package on the host
        3. Ensure the package is no longer applicable

    :expectedresults: after updating the package it is no longer shown as applicable

    :parametrized: yes

    :CaseImportance: High
    """
    # check that package is applicable
    package_name = REPO_WITH_ERRATA['errata'][0]['package_name']
    applicable_packages = target_sat.cli.Package.list(
        {
            'host-id': errata_host.nailgun_host.id,
            'packages-restrict-applicable': 'true',
            'search': f'name={package_name}',
        }
    )
    start_and_wait_errata_recalculate(target_sat, errata_host)
    assert len(applicable_packages) == 1
    assert package_name in applicable_packages[0]['filename']
    # Update package from Library, i.e. Default CV
    _job_invoc = target_sat.cli.JobInvocation.create(
        {
            'feature': 'katello_errata_install',
            'search-query': f'name = {errata_host.hostname}',
            'inputs': f'errata={REPO_WITH_ERRATA["errata"][0]["id"]}',
            'organization-id': errata_host.nailgun_host.organization.id,
        }
    )
    # job invocation created, assert status
    assert 'created' in _job_invoc[0]['message']
    assert (_id := _job_invoc[0]['id'])
    assert target_sat.cli.JobInvocation().info(options={'id': _id})['status'] == 'succeeded'
    start_and_wait_errata_recalculate(target_sat, errata_host)
    # Assert that the package is no longer applicable
    applicable_packages = target_sat.cli.Package.list(
        {
            'host-id': errata_host.nailgun_host.id,
            'packages-restrict-applicable': 'true',
            'search': f'name={package_name}',
        }
    )
    assert len(applicable_packages) == 0


@pytest.mark.tier2
@pytest.mark.no_containers
@pytest.mark.rhel_ver_match('8')
def test_downgrade_applicable_package_using_default_content_view(errata_host, target_sat):
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

    :parametrized: yes

    :CaseImportance: High
    """
    # Update package from Library, i.e. Default CV
    errata_host.run(f'yum -y update {FAKE_2_CUSTOM_PACKAGE_NAME}')
    start_and_wait_errata_recalculate(target_sat, errata_host)
    # Assert that the package is not applicable
    applicable_packages = target_sat.cli.Package.list(
        {
            'host-id': errata_host.nailgun_host.id,
            'packages-restrict-applicable': 'true',
            'search': f'name={FAKE_2_CUSTOM_PACKAGE_NAME}',
        }
    )
    assert len(applicable_packages) == 0
    # Downgrade package
    errata_host.run(f'yum -y downgrade {FAKE_1_CUSTOM_PACKAGE}')
    start_and_wait_errata_recalculate(target_sat, errata_host)
    # check that package is applicable
    applicable_packages = target_sat.cli.Package.list(
        {
            'host-id': errata_host.nailgun_host.id,
            'packages-restrict-applicable': 'true',
            'search': f'name={FAKE_2_CUSTOM_PACKAGE_NAME}',
        }
    )
    assert len(applicable_packages) == 1
    assert FAKE_2_CUSTOM_PACKAGE_NAME in applicable_packages[0]['filename']


@pytest.mark.tier2
@pytest.mark.rhel_ver_match('8')
def test_install_applicable_package_to_registerd_host(errata_host, target_sat):
    """Installing an older package to an already registered host should show the newer package
    and errata as applicable and installable.

    :id: 519bfe91-cf86-4d6e-94ef-aaf3e5d40a81

    :setup: Register a host to default org with Library,
            Remove the newer package version if present

    :steps:
        1. Ensure package is not applicable
        2. Install package that has errata
        3. Ensure the expected package is applicable

    :expectedresults: Installed package shows errata as applicable and installable

    :parametrized: yes

    :CaseImportance: Medium
    """
    errata_host.run(f'yum -y remove {FAKE_2_CUSTOM_PACKAGE_NAME}')
    start_and_wait_errata_recalculate(target_sat, errata_host)
    # Assert that the package is not applicable
    applicable_packages = target_sat.cli.Package.list(
        {
            'host-id': errata_host.nailgun_host.id,
            'packages-restrict-applicable': 'true',
            'search': f'name={FAKE_2_CUSTOM_PACKAGE_NAME}',
        }
    )
    assert len(applicable_packages) == 0
    errata_host.run(f'yum -y install {FAKE_1_CUSTOM_PACKAGE}')
    start_and_wait_errata_recalculate(target_sat, errata_host)
    # check that package is applicable
    applicable_packages = target_sat.cli.Package.list(
        {
            'host-id': errata_host.nailgun_host.id,
            'packages-restrict-applicable': 'true',
            'search': f'name={FAKE_2_CUSTOM_PACKAGE_NAME}',
        }
    )
    assert len(applicable_packages) == 1
    assert FAKE_2_CUSTOM_PACKAGE_NAME in applicable_packages[0]['filename']


@pytest.mark.tier2
@pytest.mark.no_containers
@pytest.mark.rhel_ver_match('8')
def test_downgrading_package_shows_errata_from_library(
    errata_host, module_sca_manifest_org, target_sat
):
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

    :parametrized: yes

    :CaseImportance: High
    """
    # Update package from Library, i.e. Default CV
    errata_host.run(f'yum -y install {FAKE_2_CUSTOM_PACKAGE}')
    start_and_wait_errata_recalculate(target_sat, errata_host)
    applicable_packages = target_sat.cli.Package.list(
        {
            'host-id': errata_host.nailgun_host.id,
            'packages-restrict-applicable': 'true',
            'search': f'name={FAKE_2_CUSTOM_PACKAGE_NAME}',
        }
    )
    assert len(applicable_packages) == 0
    # Downgrade package
    errata_host.run(f'yum -y downgrade {FAKE_1_CUSTOM_PACKAGE}')
    start_and_wait_errata_recalculate(target_sat, errata_host)
    param = {
        'errata-restrict-applicable': 1,
        'per-page': PER_PAGE_LARGE,
    }
    errata_ids = get_errata_ids(target_sat, param)
    assert settings.repos.yum_6.errata[2] in errata_ids


@pytest.mark.tier2
def test_errata_list_by_contentview_filter(module_sca_manifest_org, module_target_sat):
    """Hammer command to list errata should take filter ID into consideration.

    :id: e9355a92-8354-4853-a806-d388ed32d73e

    :setup: Any repo with some errata in it

    :steps:
        1. Sync a repo, add it to a CV
        2. Get the count of errata list
        3. Create a CV filter, add an errata and check the errata list count

    :expectedresults: Errata count using CV filter ID should change

    :CaseImportance: High

    :customerscenario: true

    :BZ: 1785146
    """
    product = module_target_sat.api.Product(organization=module_sca_manifest_org).create()
    repo = module_target_sat.cli_factory.make_repository(
        {'content-type': 'yum', 'product-id': product.id, 'url': REPO_WITH_ERRATA['url']}
    )
    module_target_sat.cli.Repository.synchronize({'id': repo.id})
    lce = module_target_sat.api.LifecycleEnvironment(organization=module_sca_manifest_org).create()
    cv = module_target_sat.api.ContentView(
        organization=module_sca_manifest_org, repository=[repo.id]
    ).create()
    cv_publish_promote(module_target_sat, cv, module_sca_manifest_org, lce)
    errata_count = len(
        module_target_sat.cli.Erratum.list(
            {
                'organization-id': module_sca_manifest_org.id,
                'content-view-id': cv.id,
            }
        )
    )
    cvf = module_target_sat.api.ErratumContentViewFilter(content_view=cv, inclusion=True).create()
    errata_id = module_target_sat.api.Errata().search(
        query={'search': f'errata_id="{settings.repos.yum_9.errata[0]}"'}
    )[0]
    module_target_sat.api.ContentViewFilterRule(content_view_filter=cvf, errata=errata_id).create()
    cv.publish()
    cv_version_info = cv.read().version[1].read()
    errata_count_cvf = len(
        module_target_sat.cli.Erratum.list(
            {
                'organization-id': module_sca_manifest_org.id,
                'content-view-id': cv.id,
                'content-view-version-id': cv_version_info.id,
                'content-view-filter-id': cvf.id,
            }
        )
    )
    assert errata_count != errata_count_cvf


@pytest.mark.rhel_ver_match('8')
def test_positive_verify_errata_recalculate_tasks(target_sat, errata_host):
    """Verify 'Actions::Katello::Applicability::Hosts::BulkGenerate' tasks proceed on 'worker-hosts-queue-1.service'

    :id: d5f89df2-b8fb-4aec-839d-b548b0aadc0c

    :setup: Register host which has applicable errata with satellite

    :steps:
        1. Run 'hammer host errata recalculate --host-id NUMBER' (will trigger inside errata_host fixture)
        2. Check systemctl or journalctl or /var/log/messages for 'dynflow-sidekiq@worker-hosts-queue-1.service'

    :expectedresults: worker-hosts-queue-1 should proceed with task and this can be cross verify using unique PID

    :customerscenario: true

    :BZ: 2249736
    """
    # Recalculate errata command has triggered inside errata_host fixture

    # get PID of 'worker-hosts-queue-1' from /var/log/messages
    message_log = target_sat.execute(
        'grep "dynflow-sidekiq@worker-hosts-queue-1" /var/log/messages | tail -1'
    )
    assert message_log.status == 0
    pattern_1 = r'\[(.*?)\]'  # pattern to capture PID of 'worker-hosts-queue-1'
    match = re.search(pattern_1, message_log.stdout)
    pid_log_message = match.group(1)

    # get PID of 'worker-hosts-queue-1' from systemctl command output
    systemctl_log = target_sat.execute(
        'systemctl status dynflow-sidekiq@worker-hosts-queue-1.service | grep -i "Main PID:"'
    )
    assert systemctl_log.status == 0
    pattern_2 = r'\: (.*?) \('  # pattern to capture PID of 'worker-hosts-queue-1'
    match = re.search(pattern_2, systemctl_log.stdout)
    pid_systemctl_cmd = match.group(1)

    assert pid_log_message == pid_systemctl_cmd
