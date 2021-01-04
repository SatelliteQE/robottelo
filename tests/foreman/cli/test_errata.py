"""CLI Tests for the errata management feature

:Requirement: Errata

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: ErrataManagement

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from datetime import datetime
from datetime import timedelta
from operator import itemgetter

import pytest
from fauxfactory import gen_string
from nailgun import entities

from robottelo import ssh
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
from robottelo.cli.factory import make_product
from robottelo.cli.factory import make_repository
from robottelo.cli.factory import make_role
from robottelo.cli.factory import make_user
from robottelo.cli.factory import setup_org_for_a_custom_repo
from robottelo.cli.factory import setup_org_for_a_rh_repo
from robottelo.cli.filter import Filter
from robottelo.cli.host import Host
from robottelo.cli.hostcollection import HostCollection
from robottelo.cli.org import Org
from robottelo.cli.repository import Repository
from robottelo.cli.repository_set import RepositorySet
from robottelo.cli.task import Task
from robottelo.cli.user import User
from robottelo.config import settings
from robottelo.constants import DISTRO_RHEL7
from robottelo.constants import FAKE_0_ERRATA_ID
from robottelo.constants import FAKE_0_YUM_ERRATUM_COUNT
from robottelo.constants import FAKE_1_CUSTOM_PACKAGE
from robottelo.constants import FAKE_1_CUSTOM_PACKAGE_NAME
from robottelo.constants import FAKE_1_ERRATA_ID
from robottelo.constants import FAKE_1_YUM_ERRATUM_COUNT
from robottelo.constants import FAKE_2_CUSTOM_PACKAGE
from robottelo.constants import FAKE_2_ERRATA_ID
from robottelo.constants import FAKE_3_ERRATA_ID
from robottelo.constants import FAKE_3_YUM_ERRATUM_COUNT
from robottelo.constants import FAKE_4_CUSTOM_PACKAGE
from robottelo.constants import FAKE_4_CUSTOM_PACKAGE_NAME
from robottelo.constants import FAKE_5_CUSTOM_PACKAGE
from robottelo.constants import FAKE_5_ERRATA_ID
from robottelo.constants import FAKE_6_YUM_ERRATUM_COUNT
from robottelo.constants import FAKE_9_YUM_ERRATUM
from robottelo.constants import PRDS
from robottelo.constants import REAL_4_ERRATA_CVES
from robottelo.constants import REAL_4_ERRATA_ID
from robottelo.constants import REPOS
from robottelo.constants import REPOSET
from robottelo.constants.repos import FAKE_1_YUM_REPO
from robottelo.constants.repos import FAKE_2_YUM_REPO
from robottelo.constants.repos import FAKE_3_YUM_REPO
from robottelo.constants.repos import FAKE_6_YUM_REPO
from robottelo.constants.repos import FAKE_9_YUM_REPO
from robottelo.vm import VirtualMachine


ERRATUM_MAX_IDS_INFO = 10

CUSTOM_REPO_URL = FAKE_9_YUM_REPO
CUSTOM_PACKAGE = FAKE_1_CUSTOM_PACKAGE
CUSTOM_ERRATA_ID = FAKE_2_ERRATA_ID
CUSTOM_PACKAGE_ERRATA_APPLIED = FAKE_2_CUSTOM_PACKAGE


pytestmark = [
    pytest.mark.skipif((not settings.repos_hosting_url), reason='Missing repos_hosting_url'),
    pytest.mark.run_in_one_thread,
]
# CLI Tests for the errata management feature


@pytest.fixture(scope='module')
def rh_repo(module_org, module_lce, module_cv, module_ak_cv_lce):
    # add a subscription for the Satellite Tools repo to activation key
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
    # create custom repository and add a subscription to activation key
    setup_org_for_a_custom_repo(
        {
            'url': FAKE_9_YUM_REPO,
            'organization-id': module_org.id,
            'content-view-id': module_cv.id,
            'lifecycle-environment-id': module_lce.id,
            'activationkey-id': module_ak_cv_lce.id,
        }
    )


@pytest.fixture(scope='module', params=[2])
def virtual_machines(module_org, module_ak_cv_lce, rh_repo, custom_repo, request):
    """Create and setup hosts and virtual machines."""
    virtual_machines = []
    for _ in range(request.param):
        # create VM
        virtual_machine = VirtualMachine(distro=DISTRO_RHEL7)
        virtual_machine.create()
        virtual_machines.append(virtual_machine)
        virtual_machine.install_katello_ca()
        # register content host
        virtual_machine.register_contenthost(module_org.name, module_ak_cv_lce.name)
        # enable red hat satellite repository
        virtual_machine.enable_repo(REPOS['rhst7']['id'])
        # install katello-agent
        virtual_machine.install_katello_agent()
    return virtual_machines


@pytest.fixture(scope='function')
def errata_machines(virtual_machines):
    """ Ensure VMs are in predictable state for each test"""
    for virtual_machine in virtual_machines:
        result = virtual_machine.run(f'yum erase -y {CUSTOM_PACKAGE_ERRATA_APPLIED}')
        assert result.return_code == 0
    # install the custom package on each host
    for virtual_machine in virtual_machines:
        result = virtual_machine.run(f'yum install -y {CUSTOM_PACKAGE}')
        assert result.return_code == 0
    return virtual_machines


@pytest.fixture(scope='module')
def host_collection(module_org, module_ak_cv_lce, virtual_machines):
    """Create and setup host collection."""
    host_collection = make_host_collection({'organization-id': module_org.id})
    for virtual_machine in virtual_machines:
        host = Host.info({'name': virtual_machine.hostname})
        HostCollection.add_host(
            {
                'id': host_collection['id'],
                'organization-id': module_org.id,
                'host-ids': host['id'],
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


def _is_errata_package_installed(virtual_machine):
    """Check whether errata package is installed.

    :type virtual_machine: robottelo.vm.VirtualMachine
    :rtype: bool
    """
    result = virtual_machine.run(f'rpm -q {CUSTOM_PACKAGE_ERRATA_APPLIED}')
    return True if result.return_code == 0 else False


@pytest.mark.tier3
def test_positive_install_by_hc_id_and_org_id(module_org, host_collection, errata_machines):
    """Using hc-id and org id to install an erratum in a hc

    :id: 8b22eb9d-1321-4374-8127-6d7bfdb89ad5

    :Setup: Errata synced on satellite server.

    :Steps: host-collection erratum install --errata <errata> --id <id>
        --organization-id <orgid>

    :expectedresults: Erratum is installed.

    :CaseLevel: System

    :BZ: 1457977
    """
    install_task = HostCollection.erratum_install(
        {
            'id': host_collection['id'],
            'organization-id': module_org.id,
            'errata': [CUSTOM_ERRATA_ID],
        }
    )
    Task.progress({'id': install_task[0]['id']})
    for virtual_machine in errata_machines:
        assert _is_errata_package_installed(virtual_machine)


@pytest.mark.tier3
def test_positive_install_by_hc_id_and_org_name(module_org, host_collection, errata_machines):
    """Using hc-id and org name to install an erratum in a hc

    :id: 7e5b87d7-f4d2-47b7-96aa-f86bcb64c742

    :Setup: Errata synced on satellite server.

    :Steps: host-collection erratum install --errata <errata> --id <id>
        --organization <org name>

    :expectedresults: Erratum is installed.

    :CaseLevel: System

    :BZ: 1457977
    """
    install_task = HostCollection.erratum_install(
        {
            'id': host_collection['id'],
            'organization': module_org.name,
            'errata': [CUSTOM_ERRATA_ID],
        }
    )
    Task.progress({'id': install_task[0]['id']})
    for virtual_machine in errata_machines:
        assert _is_errata_package_installed(virtual_machine)


@pytest.mark.tier3
def test_positive_install_by_hc_id_and_org_label(module_org, host_collection, errata_machines):
    """Use hc-id and org label to install an erratum in a hc

    :id: bde80181-6526-43dc-bfc2-511bb5c00676

    :Setup: errata synced on satellite server.

    :Steps: host-collection erratum install --errata <errata> --id <id>
        --organization-label <org label>

    :expectedresults: Errata is installed.

    :CaseLevel: System

    :BZ: 1457977
    """
    install_task = HostCollection.erratum_install(
        {
            'id': host_collection['id'],
            'organization-label': module_org.label,
            'errata': [CUSTOM_ERRATA_ID],
        }
    )
    Task.progress({'id': install_task[0]['id']})
    for virtual_machine in errata_machines:
        assert _is_errata_package_installed(virtual_machine)


@pytest.mark.tier3
def test_positive_install_by_hc_name_and_org_id(module_org, host_collection, errata_machines):
    """Use hc-name and org id to install an erratum in a hc

    :id: c4a38806-cbec-47cc-bbd6-228897b3b16d

    :Setup: Errata synced on satellite server.

    :Steps: host-collection erratum install --errata <errata> --name <name>
        --organization-id <orgid>

    :expectedresults: Erratum is installed.

    :CaseLevel: System

    :BZ: 1457977
    """
    install_task = HostCollection.erratum_install(
        {
            'name': host_collection['name'],
            'organization-id': module_org.id,
            'errata': [CUSTOM_ERRATA_ID],
        }
    )
    Task.progress({'id': install_task[0]['id']})
    for virtual_machine in errata_machines:
        assert _is_errata_package_installed(virtual_machine)


@pytest.mark.tier3
def test_positive_install_by_hc_name_and_org_name(module_org, host_collection, errata_machines):
    """Use hc name and org name to install an erratum in a hc

    :id: 501319ea-9d3c-4329-9405-4366ce6ee797

    :Setup: Errata synced on satellite server.

    :Steps: host-collection erratum install --errata <errata> --name <name>
        --organization <org name>

    :expectedresults: Erratum is installed.

    :CaseLevel: System

    :BZ: 1457977
    """
    install_task = HostCollection.erratum_install(
        {
            'name': host_collection['name'],
            'organization': module_org.name,
            'errata': [CUSTOM_ERRATA_ID],
        }
    )
    Task.progress({'id': install_task[0]['id']})
    for virtual_machine in errata_machines:
        assert _is_errata_package_installed(virtual_machine)


@pytest.mark.tier3
def test_positive_install_by_hc_name_and_org_label(module_org, host_collection, errata_machines):
    """Use hc-name and org label to install an erratum in a hc

    :id: 12287827-44df-4dda-872a-ac7e416e8bd7

    :Setup: Errata synced on satellite server.

    :Steps: host-collection erratum install --errata <errata> --name <name>
        --organization-label <org label>

    :expectedresults: Erratum is installed.

    :CaseLevel: System

    :BZ: 1457977
    """
    install_task = HostCollection.erratum_install(
        {
            'name': host_collection['name'],
            'organization-label': module_org.label,
            'errata': [CUSTOM_ERRATA_ID],
        }
    )
    Task.progress({'id': install_task[0]['id']})
    for virtual_machine in errata_machines:
        assert _is_errata_package_installed(virtual_machine)


@pytest.mark.tier3
def test_negative_install_by_hc_id_without_errata_info(
    module_org, host_collection, errata_machines
):
    """Attempt to install an erratum in a hc using hc-id and not
    specifying the erratum info

    :id: 3635698d-4f09-4a60-91ea-1957e5949750

    :Setup: Errata synced on satellite server.

    :Steps: host-collection erratum install --id <id> --organization-id
        <orgid>

    :expectedresults: Error message thrown.

    :CaseImportance: Low

    :CaseLevel: System
    """
    for virtual_machine in errata_machines:
        result = virtual_machine.run(f'yum install -y {CUSTOM_PACKAGE}')
        assert result.return_code == 0
    with pytest.raises(CLIReturnCodeError, match="Error: Option '--errata' is required"):
        HostCollection.erratum_install(
            {'id': host_collection['id'], 'organization-id': module_org.id}
        )


@pytest.mark.tier3
def test_negative_install_by_hc_name_without_errata_info(
    module_org, host_collection, errata_machines
):
    """Attempt to install an erratum in a hc using hc-name and not
    specifying the erratum info

    :id: 12d78bca-efd1-407a-9bd3-f989c2bda6a8

    :Setup: Errata synced on satellite server.

    :Steps: host-collection erratum install --name <name> --organization-id
        <orgid>

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
    """Attempt to install an erratum in a hc by not specifying hc
    info. This test only works with two or more HC; see BZ#1928281.
    We have the one from the fixture, just need to create one more at the start of the test.

    :id: 753d36f0-d19b-494d-a247-ce2d61c4cf74

    :Setup: Errata synced on satellite server.

    :Steps: host-collection erratum install --errata <errata>
        --organization-id <orgid>

    :expectedresults: Error message thrown.

    :CaseImportance: Low

    :CaseLevel: System
    """
    make_host_collection({'organization-id': module_org.id})
    with pytest.raises(CLIReturnCodeError):
        HostCollection.erratum_install(
            {'organization-id': module_org.id, 'errata': [CUSTOM_ERRATA_ID]}
        )


@pytest.mark.tier3
def test_negative_install_by_hc_id_without_org_info(module_org, host_collection):
    """Attempt to install an erratum in a hc using hc-id and not
    specifying org info

    :id: b7d32bb3-9c5f-452b-b421-f8e9976ca52c

    :Setup: Errata synced on satellite server.

    :Steps: host-collection erratum install --errata <errata> --id <id>

    :expectedresults: Error message thrown.

    :CaseImportance: Low

    :CaseLevel: System
    """
    with pytest.raises(CLIReturnCodeError, match='Error: Could not find organization'):
        HostCollection.erratum_install({'id': host_collection['id'], 'errata': [CUSTOM_ERRATA_ID]})


@pytest.mark.tier3
def test_negative_install_by_hc_name_without_org_info(module_org, host_collection):
    """Attempt to install an erratum in a hc without specifying org
    info

    :id: 991f5b61-a4d1-444c-8a21-8ffe48e83f76

    :Setup: Errata synced on satellite server.

    :Steps: host-collection erratum install --errata <errata> --name <name>

    :expectedresults: Error message thrown.

    :CaseImportance: Low

    :CaseLevel: System
    """
    with pytest.raises(CLIReturnCodeError, match='Error: Could not find organization'):
        HostCollection.erratum_install(
            {'name': host_collection['name'], 'errata': [CUSTOM_ERRATA_ID]}
        )


@pytest.mark.tier3
@pytest.mark.upgrade
def test_positive_list_affected_chosts(module_org, errata_machines):
    """View a list of affected content hosts for an erratum

    :id: 3b592253-52c0-4165-9a48-ba55287e9ee9

    :Setup: Errata synced on satellite server, custom package installed on errata hosts.

    :Steps: host list --search "applicable_errata = <erratum_id>"
        --organization-id=<org_id>

    :expectedresults: List of affected content hosts for an erratum is
        displayed.

    :CaseAutomation: Automated
    """
    result = Host.list(
        {
            'search': f'applicable_errata = {FAKE_2_ERRATA_ID}',
            'organization-id': module_org.id,
            'fields': 'Name',
        }
    )
    result = [item['name'] for item in result]
    for virtual_machine in errata_machines:
        assert (
            virtual_machine.hostname in result
        ), "VM host name not found in list of applicable hosts"


@pytest.mark.tier3
def test_install_errata_to_one_host(module_org, errata_machines, host_collection):
    """Install an erratum to one of the hosts in a host collection.

    :id: bfcee2de-3448-497e-a696-fcd30cea9d33

    :expectedresults: Errata was successfully installed in only one of the hosts in
        the host collection


    :Setup: Errata synced on satellite server, custom package installed on errata hosts.

    :Steps:
        1. Remove FAKE_2_CUSTOM_PACKAGE_NAME packages from one host
        2. host-collection erratum install --errata <errata> --id <id>
            --organization <org name>
        3. Assert first host does not have any FAKE_2_CUSTOM_PACKAGE_NAME packages.
        4. Assert second host does have FAKE_2_CUSTOM_PACKAGE

    :expectedresults: Erratum is only installed on one host.

    :BZ: 1810774
    """
    # Remove any walrus package on first VM to remove need for CUSTOM_ERRATA_ID
    result = errata_machines[0].run(f'yum erase -y {FAKE_1_CUSTOM_PACKAGE_NAME}')
    assert result.return_code == 0, "Failed to erase the RPM"
    # Install CUSTOM_ERRATA_ID to the host collection
    install_task = HostCollection.erratum_install(
        {
            'id': host_collection['id'],
            'organization': module_org.name,
            'errata': [CUSTOM_ERRATA_ID],
        }
    )
    Task.progress({'id': install_task[0]['id']})
    # Assert first host does not have any FAKE_1_CUSTOM_PACKAGE_NAME packages
    result = errata_machines[0].run(f'rpm -q {FAKE_1_CUSTOM_PACKAGE_NAME}')
    assert result.return_code == 1, "Unwanted custom package found."
    # Assert second host does have FAKE_2_CUSTOM_PACKAGE
    result = errata_machines[1].run(f'rpm -q {FAKE_2_CUSTOM_PACKAGE}')
    assert result.return_code == 0, "Expected custom package not found."


@pytest.mark.tier3
def test_positive_list_affected_chosts_by_erratum_restrict_flag(
    module_org, module_cv, module_lce, errata_machines
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
    # Create list of uninstallable errata by removing FAKE_2_ERRATA_ID a.k.a CUSTOM_ERRATA_ID
    UNINSTALLABLE = [erratum for erratum in FAKE_9_YUM_ERRATUM if erratum != FAKE_2_ERRATA_ID]
    # Check search for only installable errata
    erratum_list = Erratum.list(
        {
            'errata-restrict-installable': 1,
            'content-view-id': module_cv.id,
            'lifecycle-environment-id': module_lce.id,
            'organization-id': module_org.id,
            'per-page': 1000,
        }
    )
    # Assert the expected installable errata is in the list
    erratum_id_list = [erratum['errata-id'] for erratum in erratum_list]
    assert CUSTOM_ERRATA_ID in erratum_id_list, "Errata not found in list of installable errata"
    # Assert the uninstallable errata are not in the list
    for erratum in UNINSTALLABLE:
        assert erratum not in erratum_id_list, "Unexpected errata found"
    # Check search of errata is not affected by installable=0 restrict flag
    erratum_list = Erratum.list(
        {
            'errata-restrict-installable': 0,
            'content-view-id': module_cv.id,
            'lifecycle-environment-id': module_lce.id,
            'organization-id': module_org.id,
            'per-page': 1000,
        }
    )
    erratum_id_list = [erratum['errata-id'] for erratum in erratum_list]
    for erratum in FAKE_9_YUM_ERRATUM:
        assert erratum in erratum_id_list, "Errata not found in list of installable errata"
    # Check list of applicable errata
    erratum_list = Erratum.list(
        {'errata-restrict-applicable': 1, 'organization-id': module_org.id, 'per-page': 1000}
    )
    erratum_id_list = [erratum['errata-id'] for erratum in erratum_list]
    assert CUSTOM_ERRATA_ID in erratum_id_list, "Errata not found in list of applicable errata"
    # Check search of errata is not affected by applicable=0 restrict flag
    erratum_list = Erratum.list(
        {'errata-restrict-applicable': 0, 'organization-id': module_org.id, 'per-page': 1000}
    )
    erratum_id_list = [erratum['errata-id'] for erratum in erratum_list]
    for erratum in FAKE_9_YUM_ERRATUM:
        assert erratum in erratum_id_list, "Errata not found in list of applicable errata"
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
    # Make rule to hide the RPM that creates the need for the installable erratum
    make_content_view_filter_rule(
        {
            'content-view-id': module_cv.id,
            'content-view-filter': 'erratum_restrict_test',
            'name': FAKE_1_CUSTOM_PACKAGE_NAME,
        }
    )
    # Publish the version with the filter
    ContentView.publish({'id': module_cv.id})
    # Need to promote the last version published
    content_view_version = ContentView.info({'id': module_cv.id})['versions'][-1]
    ContentView.version_promote(
        {
            'id': content_view_version['id'],
            'organization-id': module_org.id,
            'to-lifecycle-environment-id': module_lce.id,
        }
    )
    # Check that the installable erratum is no longer present in the list
    erratum_list = Erratum.list(
        {
            'errata-restrict-installable': 0,
            'content-view-id': module_cv.id,
            'lifecycle-environment-id': module_lce.id,
            'organization-id': module_org.id,
            'per-page': 1000,
        }
    )
    # Assert the expected erratum is no longer in the list
    erratum_id_list = [erratum['errata-id'] for erratum in erratum_list]
    assert (
        CUSTOM_ERRATA_ID not in erratum_id_list
    ), "Errata not found in list of installable errata"
    # Check CUSTOM_ERRATA_ID still applicable
    erratum_list = Erratum.list(
        {'errata-restrict-applicable': 1, 'organization-id': module_org.id, 'per-page': 1000}
    )
    # Assert the expected erratum is in the list
    erratum_id_list = [erratum['errata-id'] for erratum in erratum_list]
    assert CUSTOM_ERRATA_ID in erratum_id_list, "Errata not found in list of applicable errata"
    # Clean up by removing the CV filter
    ContentViewFilter.delete(
        {
            'content-view-id': module_cv.id,
            'name': cv_filter['name'],
            'organization-id': module_org.id,
        }
    )


@pytest.mark.tier3
def test_host_errata_search_commands(
    module_org, module_cv, module_lce, host_collection, errata_machines
):
    """View a list of affected hosts for security (RHSA) and bugfix (RHBA) errata,
    filtered with errata status and applicable flags. Applicability is calculated using the
    Library, but Installability is calculated using the attached CV, and is subject to the
    CV's own filtering.

    :id: 07757a77-7ab4-4020-99af-2beceb023266

    :Setup: Errata synced on satellite server, custom package installed on errata hosts.

    :Steps:
        1.  host list --search "errata_status = errata_needed"
        2.  host list --search "errata_status = security_needed"
        3.  host list --search "applicable_errata = RHBA-2012:1030"
        4.  host list --search "applicable_errata = RHSA-2012:0055"
        5.  host list --search "applicable_rpms = kangaroo-0.3-1.noarch"
        6.  host list --search "applicable_rpms = walrus-5.21-1.noarch"
        7.  Create filter & rule to hide RPM (applicable vs. installable test)
        8.  Repeat steps 3 and 5, but 5 expects host name not found.

    :expectedresults: The hosts are correctly listed for RHSA and RHBA errata.

    """
    # note time for later wait_for_tasks include 2 mins margin of safety.
    timestamp = (datetime.utcnow() - timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M")
    # Install kangaroo-0.2 on first VM to create a need for RHBA-2012:1030
    # Update walrus on first VM to remove its need for RHSA-2012:0055
    result = ssh.command(
        f'yum install -y {FAKE_4_CUSTOM_PACKAGE} {FAKE_2_CUSTOM_PACKAGE}',
        errata_machines[0].ip_addr,
    )
    assert result.return_code == 0, "Failed to install RPM"
    # Wait for upload profile event (in case Satellite system slow)
    host = entities.Host().search(query={'search': f'name={errata_machines[0].hostname}'})
    wait_for_tasks(
        search_query='label = Actions::Katello::Host::UploadProfiles'
        ' and resource_id = {}'
        ' and started_at >= "{}"'.format(host[0].id, timestamp),
        search_rate=15,
        max_tries=10,
    )
    assert result.return_code == 0, "Failed to install RPM"
    # Step 1: Search for hosts that require RHBA errata
    result = Host.list(
        {
            'search': 'errata_status = errata_needed',
            'organization-id': module_org.id,
            'per-page': 1000,
        }
    )
    result = [item['name'] for item in result]
    assert errata_machines[0].hostname in result
    assert errata_machines[1].hostname not in result
    # Step 2: Search for hosts that require RHSA errata
    result = Host.list(
        {
            'search': 'errata_status = security_needed',
            'organization-id': module_org.id,
            'per-page': 1000,
        }
    )
    result = [item['name'] for item in result]
    assert errata_machines[0].hostname not in result
    assert errata_machines[1].hostname in result
    # Step 3: Search for hosts that have RHBA-2012:1030 applicable
    result = Host.list(
        {
            'search': f'applicable_errata = {FAKE_5_ERRATA_ID}',
            'organization-id': module_org.id,
            'per-page': 1000,
        }
    )
    result = [item['name'] for item in result]
    assert errata_machines[0].hostname in result
    assert errata_machines[1].hostname not in result
    # Step 4: Search for hosts that have RHSA-2012:0055 applicable
    result = Host.list(
        {
            'search': f'applicable_errata = {FAKE_2_ERRATA_ID}',
            'organization-id': module_org.id,
            'per-page': 1000,
        }
    )
    result = [item['name'] for item in result]
    assert errata_machines[0].hostname not in result
    assert errata_machines[1].hostname in result
    # Step 5: Search for hosts that have RPM for RHBA-2012:1030 applicable
    result = Host.list(
        {
            'search': f'applicable_rpms = {FAKE_5_CUSTOM_PACKAGE}',
            'organization-id': module_org.id,
            'per-page': 1000,
        }
    )
    result = [item['name'] for item in result]
    assert errata_machines[0].hostname in result
    assert errata_machines[1].hostname not in result
    # Step 6: Search for hosts that have RPM for RHSA-2012:0055 applicable
    result = Host.list(
        {
            'search': f'applicable_rpms = {FAKE_2_CUSTOM_PACKAGE}',
            'organization-id': module_org.id,
            'per-page': 1000,
        }
    )
    result = [item['name'] for item in result]
    assert errata_machines[0].hostname not in result
    assert errata_machines[1].hostname in result
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
    # Make rule to hide the RPM that indicates the erratum is installable
    make_content_view_filter_rule(
        {
            'content-view-id': module_cv.id,
            'content-view-filter': 'erratum_search_test',
            'name': f'{FAKE_4_CUSTOM_PACKAGE_NAME}',
        }
    )
    # Publish the version with the filter
    ContentView.publish({'id': module_cv.id})
    # Need to promote the last version published
    content_view_version = ContentView.info({'id': module_cv.id})['versions'][-1]
    ContentView.version_promote(
        {
            'id': content_view_version['id'],
            'organization-id': module_org.id,
            'to-lifecycle-environment-id': module_lce.id,
        }
    )
    # Step 8: Run tests again. Applicable should still be true, installable should now be false
    # Search for hosts that have RPM for RHBA-2012:1030 applicable
    result = Host.list(
        {
            'search': f'applicable_rpms = {FAKE_5_CUSTOM_PACKAGE}',
            'organization-id': module_org.id,
            'per-page': 1000,
        }
    )
    result = [item['name'] for item in result]
    assert errata_machines[0].hostname in result
    assert errata_machines[1].hostname not in result
    # There is no installable_rpms flag, so its just the one test.
    # Search for hosts that show RHBA-2012:1030 installable
    result = Host.list(
        {
            'search': f'installable_errata = {FAKE_5_ERRATA_ID}',
            'organization-id': module_org.id,
            'per-page': 1000,
        }
    )
    result = [item['name'] for item in result]
    assert errata_machines[0].hostname not in result
    assert errata_machines[1].hostname not in result
    # Clean up by removing the CV filter
    ContentViewFilter.delete(
        {
            'content-view-id': module_cv.id,
            'name': cv_filter['name'],
            'organization-id': module_org.id,
        }
    )


# Hammer CLI Tests for Erratum command


ORG1_YUM_ERRATUM_COUNT = FAKE_6_YUM_ERRATUM_COUNT
ORG1_ERRATA_ID = FAKE_2_ERRATA_ID

ORG2_YUM_ERRATUM_COUNT = FAKE_1_YUM_ERRATUM_COUNT
ORG2_ERRATA_ID = FAKE_1_ERRATA_ID

ORG3_YUM_BIG_ERRATUM_COUNT = FAKE_3_YUM_ERRATUM_COUNT
ORG3_BIG_ERRATA_ID = FAKE_3_ERRATA_ID

ORG3_YUM_SMALL_ERRATUM_COUNT = FAKE_0_YUM_ERRATUM_COUNT
ORG3_SMALL_ERRATA_ID = FAKE_0_ERRATA_ID

ORG3_YUM_BIG_ERRATUM_COUNT = FAKE_3_YUM_ERRATUM_COUNT
ORG3_BIG_ERRATA_ID = FAKE_3_ERRATA_ID


@pytest.fixture(scope='class')
def org1():
    """an org with one custom product & repository"""
    org1 = entities.Organization().create()
    org1.product = entities.Product(organization=org1).create()
    repo = make_repository(
        {
            'download-policy': 'immediate',
            'organization-id': org1.id,
            'product-id': org1.product.id,
            'url': FAKE_6_YUM_REPO,
        }
    )
    Repository.synchronize({'id': repo['id']})
    return org1


@pytest.fixture(scope='class')
def org2():
    """an org with one custom product & repository"""
    org2 = entities.Organization().create()
    org2.product = entities.Product(organization=org2).create()
    repo = make_repository(
        {
            'download-policy': 'immediate',
            'organization-id': org2.id,
            'product-id': org2.product.id,
            'url': FAKE_1_YUM_REPO,
        }
    )
    Repository.synchronize({'id': repo['id']})
    return org2


@pytest.fixture(scope='class')
def org3():
    """an org with two repositories each with a custom product"""
    # product small
    org3 = entities.Organization().create()
    org3.product_small = make_product(options={'organization-id': org3.id})
    repo = make_repository(
        {
            'download-policy': 'immediate',
            'organization-id': org3.id,
            'product-id': org3.product_small['id'],
            'url': FAKE_2_YUM_REPO,
        }
    )
    Repository.synchronize({'id': repo['id']})
    # product big
    org3.product_big = make_product(options={'organization-id': org3.id})
    repo = make_repository(
        {
            'download-policy': 'immediate',
            'organization-id': org3.id,
            'product-id': org3.product_big['id'],
            'url': FAKE_3_YUM_REPO,
        }
    )
    Repository.synchronize({'id': repo['id']})
    return org3


def _get_sorted_erratum_ids_info(erratum_ids, sort_by='issued', sort_reversed=False):
    """Query hammer for erratum ids info

    :param erratum_ids: a list of errata id
    :param sort_by: the field to sort by the results (issued or updated)
    :param sort_reversed: whether the sort should be reversed
            (not ascending)
    :return: a list of errata info dict for each errata id in erratum_ids
    :type erratum_ids: list[str]
    :type sort_by: str
    :type sort_reversed: bool
    :rtype: list[dict]
    """
    if len(erratum_ids) > ERRATUM_MAX_IDS_INFO:
        raise Exception('Erratum ids length exceeded')
    erratum_info_list = []
    for errata_id in erratum_ids:
        erratum_info_list.append(Erratum.info(options={'id': errata_id}, output_format='json'))
    sorted_erratum_info_list = sorted(
        erratum_info_list, key=itemgetter(sort_by), reverse=sort_reversed
    )
    return sorted_erratum_info_list


@pytest.mark.tier3
@pytest.mark.upgrade
def test_positive_list_sort_by_issued_date(module_org):
    """Sort errata by Issued date

    :id: d838a969-d70a-43ae-9805-2e94dd985d6b

    :Setup: Errata synced on satellite server.

    :Steps:

        1. erratum list --order 'issued ASC'
        2. erratum list --order 'issued DESC'

    :expectedresults: Errata is sorted by Issued date.
    """
    sort_data = [('issued', 'ASC'), ('issued', 'DESC')]
    for sort_field, sort_order in sort_data:
        sort_text = f'{sort_field} {sort_order}'
        sort_reversed = True if sort_order == 'DESC' else False
        erratum_list = Erratum.list({'order': sort_text, 'per-page': ERRATUM_MAX_IDS_INFO})
        # note: the erratum_list, contain a list of restraint info
        # (id, errata-id, type, title) about each errata
        assert len(erratum_list) > 0
        # build a list of erratum id received from Erratum.list
        erratum_ids = [errata['id'] for errata in erratum_list]
        # build a list of errata-id field value in the same order as
        # received from Erratum.list
        errata_ids = [errata['errata-id'] for errata in erratum_list]
        # build a sorted more detailed erratum info list, that also
        # contain the sort field
        sorted_errata_info_list = _get_sorted_erratum_ids_info(
            erratum_ids, sort_by=sort_field, sort_reversed=sort_reversed
        )
        # build a list of sort field (issued/updated) values in the
        # same order as received from the detailed sorted erratum info
        # list
        sort_field_values = [errata[sort_field] for errata in sorted_errata_info_list]
        # ensure that the sort field (issued/updated) values are sorted
        # as needed
        assert sort_field_values == sorted(sort_field_values, reverse=sort_reversed)
        # build a list of errata-id field value in the same order as
        # received from the detailed sorted errata info list
        sorted_errata_ids = [errata['errata-id'] for errata in sorted_errata_info_list]
        # ensure that the errata ids received by Erratum.list is sorted
        # as needed
        assert errata_ids == sorted_errata_ids


@pytest.mark.tier3
def test_positive_list_filter_by_org_id_and_sort_by_updated_date(module_org):
    """Filter errata by org id and sort by updated date

    :id: 9b7f98ee-bbde-47b6-8727-b02550df13ae

    :Setup: Errata synced on satellite server.

    :Steps:

        1. erratum list --organization-id=<orgid> --order 'updated ASC'
        2. erratum list --organization-id=<orgid> --order 'updated DESC'

    :expectedresults: Errata is filtered by org id and sorted by updated
        date.
    """
    sort_data = [('updated', 'ASC'), ('updated', 'DESC')]
    for sort_field, sort_order in sort_data:
        sort_text = f'{sort_field} {sort_order}'
        sort_reversed = True if sort_order == 'DESC' else False
        erratum_list = Erratum.list(
            {
                'organization-id': module_org.id,
                'order': sort_text,
                'per-page': ERRATUM_MAX_IDS_INFO,
            }
        )
        # note: the erratum_list, contain a list of restraint info
        # (id, errata-id, type, title) about each errata
        assert len(erratum_list) > 0
        # build a list of erratum id received from Erratum.list
        erratum_ids = [errata['id'] for errata in erratum_list]
        # build a list of errata-id field value in the same order as
        # received from Erratum.list
        errata_ids = [errata['errata-id'] for errata in erratum_list]
        # build a sorted more detailed erratum info list, that also
        # contain the sort field
        sorted_errata_info_list = _get_sorted_erratum_ids_info(
            erratum_ids, sort_by=sort_field, sort_reversed=sort_reversed
        )
        # build a list of sort field (issued/updated) values in the
        # same order as received from the detailed sorted erratum info
        # list
        sort_field_values = [errata[sort_field] for errata in sorted_errata_info_list]
        # ensure that the sort field (issued/updated) values are sorted
        # as needed
        assert sort_field_values == sorted(sort_field_values, reverse=sort_reversed)
        # build a list of errata-id field value in the same order as
        # received from the detailed sorted errata info list
        sorted_errata_ids = [errata['errata-id'] for errata in sorted_errata_info_list]
        # ensure that the errata ids received by Erratum.list is sorted
        # as needed
        assert errata_ids == sorted_errata_ids


@pytest.mark.tier3
def test_positive_list_filter_by_org_name_and_sort_by_updated_date(module_org):
    """Filter errata by org name and sort by updated date

    :id: f202616b-cd4f-4ab2-bf2a-2788579e355a

    :Setup: Errata synced on satellite server.

    :Steps:

        1. erratum list --organization=<org name> --order 'updated ASC'
        2. erratum list --organization=<org name> --order 'updated DESC'

    :expectedresults: Errata is filtered by org name and sorted by updated
        date.
    """
    sort_data = [('updated', 'ASC'), ('updated', 'DESC')]
    for sort_field, sort_order in sort_data:
        sort_text = f'{sort_field} {sort_order}'
        sort_reversed = True if sort_order == 'DESC' else False
        erratum_list = Erratum.list(
            {
                'organization': module_org.name,
                'order': sort_text,
                'per-page': ERRATUM_MAX_IDS_INFO,
            }
        )
        # note: the erratum_list, contain a list of restraint info
        # (id, errata-id, type, title) about each errata
        assert len(erratum_list) > 0
        # build a list of erratum id received from Erratum.list
        erratum_ids = [errata['id'] for errata in erratum_list]
        # build a list of errata-id field value in the same order as
        # received from Erratum.list
        errata_ids = [errata['errata-id'] for errata in erratum_list]
        # build a sorted more detailed erratum info list, that also
        # contain the sort field
        sorted_errata_info_list = _get_sorted_erratum_ids_info(
            erratum_ids, sort_by=sort_field, sort_reversed=sort_reversed
        )
        # build a list of sort field (issued/updated) values in the
        # same order as received from the detailed sorted erratum info
        # list
        sort_field_values = [errata[sort_field] for errata in sorted_errata_info_list]
        # ensure that the sort field (issued/updated) values are sorted
        # as needed
        assert sort_field_values == sorted(sort_field_values, reverse=sort_reversed)
        # build a list of errata-id field value in the same order as
        # received from the detailed sorted errata info list
        sorted_errata_ids = [errata['errata-id'] for errata in sorted_errata_info_list]
        # ensure that the errata ids received by Erratum.list is sorted
        # as needed
        assert errata_ids == sorted_errata_ids


@pytest.mark.tier3
def test_positive_list_filter_by_org_label_and_sort_by_updated_date(module_org):
    """Filter errata by org label and sort by updated date

    :id: ce891bdf-cc2f-46e9-ab43-91527d40c3ed

    :Setup: Errata synced on satellite server.

    :Steps:

        1. erratum list --organization-label=<org_label> --order 'updated
            ASC'
        2. erratum list --organization-label=<org_label> --order 'updated
            DESC'

    :expectedresults: Errata is filtered by org label and sorted by updated
        date.
    """
    sort_data = [('updated', 'ASC'), ('updated', 'DESC')]
    for sort_field, sort_order in sort_data:
        sort_text = f'{sort_field} {sort_order}'
        sort_reversed = True if sort_order == 'DESC' else False
        erratum_list = Erratum.list(
            {
                'organization-label': module_org.label,
                'order': sort_text,
                'per-page': ERRATUM_MAX_IDS_INFO,
            }
        )
        # note: the erratum_list, contain a list of restraint info
        # (id, errata-id, type, title) about each errata
        assert len(erratum_list) > 0
        # build a list of erratum id received from Erratum.list
        erratum_ids = [errata['id'] for errata in erratum_list]
        # build a list of errata-id field value in the same order as
        # received from Erratum.list
        errata_ids = [errata['errata-id'] for errata in erratum_list]
        # build a sorted more detailed erratum info list, that also
        # contain the sort field
        sorted_errata_info_list = _get_sorted_erratum_ids_info(
            erratum_ids, sort_by=sort_field, sort_reversed=sort_reversed
        )
        # build a list of sort field (issued/updated) values in the
        # same order as received from the detailed sorted erratum info
        # list
        sort_field_values = [errata[sort_field] for errata in sorted_errata_info_list]
        # ensure that the sort field (issued/updated) values are sorted
        # as needed
        assert sort_field_values == sorted(sort_field_values, reverse=sort_reversed)
        # build a list of errata-id field value in the same order as
        # received from the detailed sorted errata info list
        sorted_errata_ids = [errata['errata-id'] for errata in sorted_errata_info_list]
        # ensure that the errata ids received by Erratum.list is sorted
        # as needed
        assert errata_ids == sorted_errata_ids


@pytest.mark.tier3
def test_positive_list_filter_by_org_id_and_sort_by_issued_date(module_org, rh_repo, custom_repo):
    """Filter errata by org id and sort by issued date

    :id: 5d0f396c-f930-4fe7-8d1e-5039a4ed359a

    :Setup: Errata synced on satellite server.

    :Steps:

        1. erratum list --organization-id=<org_id> --order 'issued ASC'
        2. erratum list --organization-id=<org_id> --order 'issued DESC'

    :expectedresults: Errata is filtered by org id and sorted by issued
        date.
    """
    sort_data = [('issued', 'ASC'), ('issued', 'DESC')]
    for sort_field, sort_order in sort_data:
        sort_text = f'{sort_field} {sort_order}'
        sort_reversed = True if sort_order == 'DESC' else False
        erratum_list = Erratum.list(
            {
                'organization-id': module_org.id,
                'order': sort_text,
                'per-page': ERRATUM_MAX_IDS_INFO,
            }
        )
        # note: the erratum_list, contain a list of restraint info
        # (id, errata-id, type, title) about each errata
        assert len(erratum_list) > 0
        # build a list of erratum id received from Erratum.list
        erratum_ids = [errata['id'] for errata in erratum_list]
        # build a list of errata-id field value in the same order as
        # received from Erratum.list
        errata_ids = [errata['errata-id'] for errata in erratum_list]
        # build a sorted more detailed erratum info list, that also
        # contain the sort field
        sorted_errata_info_list = _get_sorted_erratum_ids_info(
            erratum_ids, sort_by=sort_field, sort_reversed=sort_reversed
        )
        # build a list of sort field (issued/updated) values in the
        # same order as received from the detailed sorted erratum info
        # list
        sort_field_values = [errata[sort_field] for errata in sorted_errata_info_list]
        # ensure that the sort field (issued/updated) values are sorted
        # as needed
        assert sort_field_values == sorted(sort_field_values, reverse=sort_reversed)
        # build a list of errata-id field value in the same order as
        # received from the detailed sorted errata info list
        sorted_errata_ids = [errata['errata-id'] for errata in sorted_errata_info_list]
        # ensure that the errata ids received by Erratum.list is sorted
        # as needed
        assert errata_ids == sorted_errata_ids


@pytest.mark.tier3
def test_positive_list_filter_by_org_name_and_sort_by_issued_date(
    module_org, rh_repo, custom_repo
):
    """Filter errata by org name and sort by issued date

    :id: 22f05ac0-fefa-48c4-861d-eeed41d9b235

    :Setup: Errata synced on satellite server.

    :Steps:

        1. erratum list --organization=<org_name> --order 'issued ASC'
        2. erratum list --organization=<org_name> --order 'issued DESC'

    :expectedresults: Errata is filtered by org name and sorted by issued
        date.
    """
    sort_data = [('issued', 'ASC'), ('issued', 'DESC')]
    for sort_field, sort_order in sort_data:
        sort_text = f'{sort_field} {sort_order}'
        sort_reversed = True if sort_order == 'DESC' else False
        erratum_list = Erratum.list(
            {
                'organization': module_org.name,
                'order': sort_text,
                'per-page': ERRATUM_MAX_IDS_INFO,
            }
        )
        # note: the erratum_list, contain a list of restraint info
        # (id, errata-id, type, title) about each errata
        assert len(erratum_list) > 0
        # build a list of erratum id received from Erratum.list
        erratum_ids = [errata['id'] for errata in erratum_list]
        # build a list of errata-id field value in the same order as
        # received from Erratum.list
        errata_ids = [errata['errata-id'] for errata in erratum_list]
        # build a sorted more detailed erratum info list, that also
        # contain the sort field
        sorted_errata_info_list = _get_sorted_erratum_ids_info(
            erratum_ids, sort_by=sort_field, sort_reversed=sort_reversed
        )
        # build a list of sort field (issued/updated) values in the
        # same order as received from the detailed sorted erratum info
        # list
        sort_field_values = [errata[sort_field] for errata in sorted_errata_info_list]
        # ensure that the sort field (issued/updated) values are sorted
        # as needed
        assert sort_field_values == sorted(sort_field_values, reverse=sort_reversed)
        # build a list of errata-id field value in the same order as
        # received from the detailed sorted errata info list
        sorted_errata_ids = [errata['errata-id'] for errata in sorted_errata_info_list]
        # ensure that the errata ids received by Erratum.list is sorted
        # as needed
        assert errata_ids == sorted_errata_ids


@pytest.mark.tier3
def test_positive_list_filter_by_org_label_and_sort_by_issued_date(
    module_org, rh_repo, custom_repo
):
    """Filter errata by org label and sort by issued date

    :id: 31acb734-8705-4d3c-b05e-edfd63d1ca3b

    :Setup: Errata synced on satellite server.

    :Steps:

        1. erratum list --organization-label=<org_label> --order 'issued
            ASC'
        2. erratum list --organization-label=<org_label> --order 'issued
            DESC'

    :expectedresults: Errata is filtered by org label and sorted by issued
        date.
    """
    sort_data = [('issued', 'ASC'), ('issued', 'DESC')]
    for sort_field, sort_order in sort_data:
        sort_text = f'{sort_field} {sort_order}'
        sort_reversed = True if sort_order == 'DESC' else False
        erratum_list = Erratum.list(
            {
                'organization-label': module_org.label,
                'order': sort_text,
                'per-page': ERRATUM_MAX_IDS_INFO,
            }
        )
        # note: the erratum_list, contain a list of restraint info
        # (id, errata-id, type, title) about each errata
        assert len(erratum_list) > 0
        # build a list of erratum id received from Erratum.list
        erratum_ids = [errata['id'] for errata in erratum_list]
        # build a list of errata-id field in the same order as received
        # from Erratum.list
        errata_ids = [errata['errata-id'] for errata in erratum_list]
        # build a sorted more detailed erratum info list, that also
        # contain the sort field
        sorted_errata_info_list = _get_sorted_erratum_ids_info(
            erratum_ids, sort_by=sort_field, sort_reversed=sort_reversed
        )
        # build a list of sort field (issued/updated) values in the
        # same order as received from the detailed sorted erratum info
        # list
        sort_field_values = [errata[sort_field] for errata in sorted_errata_info_list]
        # ensure that the sort field (issued/updated) values are sorted
        # as needed
        assert sort_field_values == sorted(sort_field_values, reverse=sort_reversed)
        # build a list of errata-id field value in the same order as
        # received from the detailed sorted errata info list
        sorted_errata_ids = [errata['errata-id'] for errata in sorted_errata_info_list]
        # ensure that the errata ids received by Erratum.list is sorted
        # as needed
        assert errata_ids == sorted_errata_ids


@pytest.mark.tier3
def test_positive_list_filter_by_product_id(
    org1,
    org2,
):
    """Filter errata by product id

    :id: 7d06950a-c058-48b3-a384-c3565cbd643f

    :Setup: Errata synced on satellite server.

    :Steps: erratum list --product-id=<productid>

    :expectedresults: Errata is filtered by product id.
    """
    org1.product_erratum_list = Erratum.list({'product-id': org1.product.id, 'per-page': 1000})
    org1.product_errata_ids = {errata['errata-id'] for errata in org1.product_erratum_list}
    org2.product_erratum_list = Erratum.list({'product-id': org2.product.id, 'per-page': 1000})
    org2.product_errata_ids = {errata['errata-id'] for errata in org2.product_erratum_list}
    assert len(org1.product_errata_ids) == ORG1_YUM_ERRATUM_COUNT
    assert len(org2.product_errata_ids) == ORG2_YUM_ERRATUM_COUNT
    assert ORG1_ERRATA_ID in org1.product_errata_ids
    assert ORG2_ERRATA_ID in org2.product_errata_ids
    assert org1.product_errata_ids.intersection(org2.product_errata_ids) == set()


@pytest.mark.tier3
def test_positive_list_filter_by_product_id_and_org_id(
    org1,
    org3,
):
    """Filter errata by product id and Org id

    :id: caf14671-d8b2-4a23-8c7e-6667bb78d4b7

    :Setup: Errata synced on satellite server.

    :Steps: erratum list --product-id=<product_id>
        --organization-id=<org_id>

    :expectedresults: Errata is filtered by product id and Org id.
    """
    product_erratum_list = Erratum.list(
        {
            'organization-id': org1.id,
            'product-id': org1.product.id,
            'per-page': 1000,
        }
    )
    product_errata_ids = {errata['errata-id'] for errata in product_erratum_list}
    product_small_erratum_list = Erratum.list(
        {
            'organization-id': org3.id,
            'product-id': org3.product_small['id'],
            'per-page': 1000,
        }
    )
    product_small_errata_ids = {errata['errata-id'] for errata in product_small_erratum_list}
    product_big_erratum_list = Erratum.list(
        {
            'organization-id': org3.id,
            'product-id': org3.product_big['id'],
            'per-page': 1000,
        }
    )
    product_big_errata_ids = {errata['errata-id'] for errata in product_big_erratum_list}
    assert len(product_errata_ids) == ORG1_YUM_ERRATUM_COUNT
    assert len(product_small_errata_ids) == ORG3_YUM_SMALL_ERRATUM_COUNT
    assert len(product_big_errata_ids) == ORG3_YUM_BIG_ERRATUM_COUNT
    assert ORG1_ERRATA_ID in product_errata_ids
    assert ORG3_SMALL_ERRATA_ID in product_small_errata_ids
    assert ORG3_BIG_ERRATA_ID in product_big_errata_ids
    assert product_errata_ids.intersection(product_small_errata_ids) == set()
    assert product_errata_ids.intersection(product_big_errata_ids) == set()
    assert product_small_errata_ids.intersection(product_big_errata_ids) == set()


@pytest.mark.tier3
def test_positive_list_filter_by_product_id_and_org_name(
    org1,
    org3,
):
    """Filter errata by product id and Org name

    :id: 574a6f7e-a89e-482e-bf15-39cfd7730630

    :Setup: errata synced on satellite server.

    :Steps: erratum list --product-id=<product_id>
        --organization=<org_name>

    :expectedresults: Errata is filtered by product id and Org name.
    """
    product_erratum_list = Erratum.list(
        {
            'organization': org1.name,
            'product-id': org1.product.id,
            'per-page': 1000,
        }
    )
    product_errata_ids = {errata['errata-id'] for errata in product_erratum_list}
    product_small_erratum_list = Erratum.list(
        {
            'organization': org3.name,
            'product-id': org3.product_small['id'],
            'per-page': 1000,
        }
    )
    product_small_errata_ids = {errata['errata-id'] for errata in product_small_erratum_list}
    product_big_erratum_list = Erratum.list(
        {
            'organization': org3.name,
            'product-id': org3.product_big['id'],
            'per-page': 1000,
        }
    )
    product_big_errata_ids = {errata['errata-id'] for errata in product_big_erratum_list}
    assert len(product_errata_ids) == ORG1_YUM_ERRATUM_COUNT
    assert len(product_small_errata_ids) == ORG3_YUM_SMALL_ERRATUM_COUNT
    assert len(product_big_errata_ids) == ORG3_YUM_BIG_ERRATUM_COUNT
    assert ORG1_ERRATA_ID in product_errata_ids
    assert ORG3_SMALL_ERRATA_ID in product_small_errata_ids
    assert ORG3_BIG_ERRATA_ID in product_big_errata_ids
    assert product_errata_ids.intersection(product_small_errata_ids) == set()
    assert product_errata_ids.intersection(product_big_errata_ids) == set()
    assert product_small_errata_ids.intersection(product_big_errata_ids) == set()

    @pytest.mark.tier3
    def test_positive_list_filter_by_product_id_and_org_label(org1, org3):
        """Filter errata by product id and Org label

        :id: 7b92ee32-2386-452c-9443-65b0c233a564

        :Setup: errata synced on satellite server.

        :Steps: erratum list --product-id=<product_id>
            --organization-label=<org_label>

        :expectedresults: Errata is filtered by product id and Org label
        """
        product_erratum_list = Erratum.list(
            {
                'organization-label': org1.label,
                'product-id': org1.product.id,
                'per-page': 1000,
            }
        )
        product_errata_ids = {errata['errata-id'] for errata in product_erratum_list}
        product_small_erratum_list = Erratum.list(
            {
                'organization-label': org3.label,
                'product-id': org3.product_small['id'],
                'per-page': 1000,
            }
        )
        product_small_errata_ids = {errata['errata-id'] for errata in product_small_erratum_list}
        product_big_erratum_list = Erratum.list(
            {
                'organization-label': org3.label,
                'product-id': org3.product_big['id'],
                'per-page': 1000,
            }
        )
        product_big_errata_ids = {errata['errata-id'] for errata in product_big_erratum_list}
        assert len(product_errata_ids) == ORG1_YUM_ERRATUM_COUNT
        assert len(product_small_errata_ids) == ORG3_YUM_SMALL_ERRATUM_COUNT
        assert len(product_big_errata_ids) == ORG3_YUM_BIG_ERRATUM_COUNT
        assert ORG1_ERRATA_ID in product_errata_ids
        assert ORG3_SMALL_ERRATA_ID in product_small_errata_ids
        assert ORG3_BIG_ERRATA_ID in product_big_errata_ids
        assert product_errata_ids.intersection(product_small_errata_ids) == set()
        assert product_errata_ids.intersection(product_big_errata_ids) == set()
        assert product_small_errata_ids.intersection(product_big_errata_ids) == set()

    @pytest.mark.tier3
    def test_negative_list_filter_by_product_name(org1):
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
            Erratum.list({'product': org1.product.name, 'per-page': 1000})

    @pytest.mark.tier3
    def test_positive_list_filter_by_product_name_and_org_id(org1, org3):
        """Filter errata by product name and Org id

        :id: 53f7afa2-285d-4d40-9fdd-5013b3f02462

        :Setup: Errata synced on satellite server.

        :Steps: erratum list --product=<product_name>
            --organization-id=<org_id>

        :expectedresults: Errata is filtered by product name and Org id.
        """
        product_erratum_list = Erratum.list(
            {
                'organization-id': org1.id,
                'product': org1.name,
                'per-page': 1000,
            }
        )
        product_errata_ids = {errata['errata-id'] for errata in product_erratum_list}
        product_small_erratum_list = Erratum.list(
            {
                'organization-id': org3.id,
                'product': org3.product_small['name'],
                'per-page': 1000,
            }
        )
        product_small_errata_ids = {errata['errata-id'] for errata in product_small_erratum_list}
        product_big_erratum_list = Erratum.list(
            {
                'organization-id': org3.id,
                'product': org3.product_big['name'],
                'per-page': 1000,
            }
        )
        product_big_errata_ids = {errata['errata-id'] for errata in product_big_erratum_list}
        assert len(product_errata_ids) == ORG1_YUM_ERRATUM_COUNT
        assert len(product_small_errata_ids) == org3.product_small_erratum_count
        assert len(product_big_errata_ids) == org3.product_big_erratum_count
        assert ORG1_ERRATA_ID in product_errata_ids
        assert ORG3_SMALL_ERRATA_ID in product_small_errata_ids
        assert ORG3_BIG_ERRATA_ID in product_big_errata_ids
        assert product_errata_ids.intersection(product_small_errata_ids) == set()
        assert product_errata_ids.intersection(product_big_errata_ids) == set()
        assert product_small_errata_ids.intersection(product_big_errata_ids) == set()

    @pytest.mark.tier3
    def test_positive_list_filter_by_product_name_and_org_name(org1, org3):
        """Filter errata by product name and Org name

        :id: 8102d688-30d7-4ee5-a1aa-7e041d842a6f

        :Setup: Errata synced on satellite server.

        :Steps: erratum list --product=<product_name> --organization=<org_name>

        :expectedresults: Errata is filtered by product name and Org name.
        """
        product_erratum_list = Erratum.list(
            {
                'organization': org1.name,
                'product': org1.product['name'],
                'per-page': 1000,
            }
        )
        product_errata_ids = {errata['errata-id'] for errata in product_erratum_list}
        product_small_erratum_list = Erratum.list(
            {
                'organization': org3.name,
                'product': org3.product_small['name'],
                'per-page': 1000,
            }
        )
        product_small_errata_ids = {errata['errata-id'] for errata in product_small_erratum_list}
        product_big_erratum_list = Erratum.list(
            {
                'organization': org3.name,
                'product': org3.product_big['name'],
                'per-page': 1000,
            }
        )
        product_big_errata_ids = {errata['errata-id'] for errata in product_big_erratum_list}
        assert len(product_errata_ids) == ORG1_YUM_ERRATUM_COUNT
        assert len(product_small_errata_ids) == org3.product_small_erratum_count
        assert len(product_big_errata_ids) == org3.product_big_erratum_count
        assert ORG1_ERRATA_ID in product_errata_ids
        assert ORG3_SMALL_ERRATA_ID in product_small_errata_ids
        assert ORG3_BIG_ERRATA_ID in product_big_errata_ids
        assert product_errata_ids.intersection(product_small_errata_ids) == set()
        assert product_errata_ids.intersection(product_big_errata_ids) == set()
        assert product_small_errata_ids.intersection(product_big_errata_ids) == set()

    @pytest.mark.tier3
    def test_positive_list_filter_by_product_name_and_org_label(org1, org3):
        """Filter errata by product name and Org label

        :id: 64abb151-3f9d-4cad-b4a1-6bf0d73d8a3c

        :Setup: Errata synced on satellite server.

        :Steps: erratum list --product=<product_name>
            --organization-label=<org_label>

        :expectedresults: Errata is filtered by product name and Org label.
        """
        product_erratum_list = Erratum.list(
            {
                'organization-label': org1.label,
                'product': org1.product['name'],
                'per-page': 1000,
            }
        )
        product_errata_ids = {errata['errata-id'] for errata in product_erratum_list}
        product_small_erratum_list = Erratum.list(
            {
                'organization-label': org3.label,
                'product': org3.product_small['name'],
                'per-page': 1000,
            }
        )
        product_small_errata_ids = {errata['errata-id'] for errata in product_small_erratum_list}
        product_big_erratum_list = Erratum.list(
            {
                'organization-label': org3.label,
                'product': org3.product_big['name'],
                'per-page': 1000,
            }
        )
        product_big_errata_ids = {errata['errata-id'] for errata in product_big_erratum_list}
        assert len(product_errata_ids) == ORG1_YUM_ERRATUM_COUNT
        assert len(product_small_errata_ids) == org3.product_small_erratum_count
        assert len(product_big_errata_ids) == org3.product_big_erratum_count
        assert ORG1_ERRATA_ID in product_errata_ids
        assert ORG3_SMALL_ERRATA_ID in product_small_errata_ids
        assert ORG3_BIG_ERRATA_ID in product_big_errata_ids
        assert product_errata_ids.intersection(product_small_errata_ids) == set()
        assert product_errata_ids.intersection(product_big_errata_ids) == set()
        assert product_small_errata_ids.intersection(product_big_errata_ids) == set()

    @pytest.mark.tier3
    def test_positive_list_filter_by_org_id(
        org1,
        org2,
    ):
        """Filter errata by Org id

        :id: eeb2b409-89dc-4576-9f89-520cf7152a5a

        :Setup: Errata synced on satellite server.

        :Steps: erratum list --organization-id=<orgid>

        :expectedresults: Errata is filtered by Org id.
        """
        org1_erratum_list = Erratum.list({'organization-id': org1.id, 'per-page': 1000})
        org1_errata_ids = {errata['errata-id'] for errata in org1_erratum_list}
        org2_erratum_list = Erratum.list({'organization-id': org2.id, 'per-page': 1000})
        org2_errata_ids = {errata['errata-id'] for errata in org2_erratum_list}
        assert len(org1_errata_ids) == ORG1_YUM_ERRATUM_COUNT
        assert len(org2_errata_ids) == ORG2_YUM_ERRATUM_COUNT
        assert ORG1_ERRATA_ID in org1_errata_ids
        assert ORG2_ERRATA_ID in org2_errata_ids
        assert org1_errata_ids.intersection(org2_errata_ids) == set()

    @pytest.mark.tier3
    def test_positive_list_filter_by_org_name(
        org1,
        org2,
    ):
        """Filter errata by Org name

        :id: f2b20bb5-0938-4c7b-af95-d2b3e2b36581

        :Setup: Errata synced on satellite server.

        :Steps: erratum list --organization=<org name>

        :expectedresults: Errata is filtered by Org name.
        """
        org1_erratum_list = Erratum.list({'organization': org1.name, 'per-page': 1000})
        org1_errata_ids = {errata['errata-id'] for errata in org1_erratum_list}
        org2_erratum_list = Erratum.list({'organization': org2.name, 'per-page': 1000})
        org2_errata_ids = {errata['errata-id'] for errata in org2_erratum_list}
        assert len(org1_errata_ids) == ORG1_YUM_ERRATUM_COUNT
        assert len(org2_errata_ids) == ORG2_YUM_ERRATUM_COUNT
        assert ORG1_ERRATA_ID in org1_errata_ids
        assert ORG2_ERRATA_ID in org2_errata_ids
        assert org1_errata_ids.intersection(org2_errata_ids) == set()

    @pytest.mark.tier3
    def test_positive_list_filter_by_org_label(
        org1,
        org2,
    ):
        """Filter errata by Org label

        :id: 398123f5-d3ad-4a16-ac5d-e157d6d67595

        :Setup: Errata synced on satellite server.

        :Steps: erratum list --organization-label=<org_label>

        :expectedresults: Errata is filtered by Org label.
        """
        org1_erratum_list = Erratum.list({'organization-label': org1.label, 'per-page': 1000})
        org1_errata_ids = {errata['errata-id'] for errata in org1_erratum_list}
        org2_erratum_list = Erratum.list({'organization-label': org2.label, 'per-page': 1000})
        org2_errata_ids = {errata['errata-id'] for errata in org2_erratum_list}
        assert len(org1_errata_ids) == ORG1_YUM_ERRATUM_COUNT
        assert len(org2_errata_ids) == ORG2_YUM_ERRATUM_COUNT
        assert ORG1_ERRATA_ID in org1_errata_ids
        assert ORG2_ERRATA_ID in org2_errata_ids
        assert org1_errata_ids.intersection(org2_errata_ids) == set()

    @pytest.mark.run_in_one_thread
    @pytest.mark.tier3
    def test_positive_list_filter_by_cve(module_org):
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
        erratum = Erratum.list({'repository-id': repository_info['id']})
        errata_ids = [errata['errata-id'] for errata in erratum]
        assert REAL_4_ERRATA_ID in errata_ids
        for errata_cve in REAL_4_ERRATA_CVES:
            cve_erratum = Erratum.list({'cve': errata_cve})
            cve_errata_ids = [cve_errata['errata-id'] for cve_errata in cve_erratum]
            assert REAL_4_ERRATA_ID in cve_errata_ids

    @pytest.mark.tier3
    @pytest.mark.upgrade
    def test_positive_user_permission(module_org):
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
        org = org3
        product = org3.product_small
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
        role = make_role({'organization-ids': org['id']})
        # create a filter with the required permissions for role with product
        # one only
        make_filter(
            {
                'permission-ids': user_required_permissions_ids,
                'role-id': role['id'],
                'search': f"name = {product['name']}",
            }
        )
        # create a new user and assign him the created role permissions
        user = make_user(
            {
                'admin': False,
                'login': user_name,
                'password': user_password,
                'organization-ids': [org['id']],
                'default-organization-id': org['id'],
            }
        )
        User.add_role({'id': user['id'], 'role-id': role['id']})
        # make sure the user is not admin and has only the permissions assigned
        user = User.info({'id': user['id']})
        assert user['admin'] == 'no'
        assert set(user['roles']) == {role['name']}
        # try to get organization info
        # get the info as admin user first
        org_info = Org.info({'id': org['id']})
        assert org['id'] == org_info['id']
        assert org['name'] == org_info['name']
        # get the organization info as the created user
        with pytest.raises(CLIReturnCodeError) as context:
            Org.with_user(user_name, user_password).info({'id': org['id']})
        assert (
            'Missing one of the required permissions: view_organizations' in context.value.stderr
        )
        # try to get the erratum products list by organization id only
        # ensure that all products erratum are accessible by admin user
        admin_org_erratum_info_list = Erratum.list({'organization-id': org['id']})
        admin_org_errata_ids = [errata['errata-id'] for errata in admin_org_erratum_info_list]
        assert org3.product_small_errata_id in admin_org_errata_ids
        assert org3.product_big_errata_id in admin_org_errata_ids
        org_erratum_count = org3.product_small_erratum_count + org3.product_big_erratum_count
        assert len(admin_org_errata_ids) == org_erratum_count
        # ensure that the created user see only the erratum product that was
        # assigned in permissions
        user_org_erratum_info_list = Erratum.with_user(user_name, user_password).list(
            {'organization-id': org['id']}
        )
        user_org_errata_ids = [errata['errata-id'] for errata in user_org_erratum_info_list]
        assert len(user_org_errata_ids) == org3.product_small_erratum_count
        assert org3.product_small_errata_id in user_org_errata_ids
        assert org3.product_big_errata_id not in user_org_errata_ids

    @pytest.mark.tier3
    def test_positive_check_errata_dates(module_org):
        """Check for errata dates in `hammer erratum list`

        :id: b19286ae-bdb4-4319-87d0-5d3ff06c5f38

        :expectedresults: Display errata date when using hammer erratum list

        :CaseImportance: High

        :BZ: 1695163
        """
        custom_product = make_product({'organization-id': module_org.id})
        custom_repo = make_repository(
            {'content-type': 'yum', 'product-id': custom_product['id'], 'url': FAKE_1_YUM_REPO}
        )
        # Synchronize custom repository
        Repository.synchronize({'id': custom_repo['id']})
        result = Erratum.list(options={'per-page': '5', 'fields': 'Issued'})
        assert 'issued' in result[0]
        # Verify any errata ISSUED date from stdout
        validate_issued_date = datetime.datetime.strptime(result[0]['issued'], '%Y-%m-%d').date()
        assert isinstance(validate_issued_date, datetime.date)

        result = Erratum.list(options={'per-page': '5', 'fields': 'Updated'})
        assert 'updated' in result[0]
        # Verify any errata UPDATED date from stdout
        validate_updated_date = datetime.datetime.strptime(result[0]['updated'], '%Y-%m-%d').date()
        assert isinstance(validate_updated_date, datetime.date)
