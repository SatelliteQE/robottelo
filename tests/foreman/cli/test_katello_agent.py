"""CLI tests for ``katello-agent``.

:Requirement: Host

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: Katello-agent

:Assignee: gtalreja

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import time

import pytest

from robottelo.api.utils import wait_for_errata_applicability_task
from robottelo.cleanup import vm_cleanup
from robottelo.cli.activationkey import ActivationKey
from robottelo.cli.factory import make_activation_key
from robottelo.cli.factory import make_content_view
from robottelo.cli.factory import make_host_collection
from robottelo.cli.factory import make_lifecycle_environment
from robottelo.cli.factory import make_org
from robottelo.cli.factory import setup_org_for_a_custom_repo
from robottelo.cli.factory import setup_org_for_a_rh_repo
from robottelo.cli.host import Host
from robottelo.cli.hostcollection import HostCollection
from robottelo.constants import DISTRO_RHEL7
from robottelo.constants import FAKE_0_CUSTOM_PACKAGE_GROUP
from robottelo.constants import FAKE_0_CUSTOM_PACKAGE_GROUP_NAME
from robottelo.constants import FAKE_0_CUSTOM_PACKAGE_NAME
from robottelo.constants import FAKE_1_CUSTOM_PACKAGE
from robottelo.constants import FAKE_1_CUSTOM_PACKAGE_NAME
from robottelo.constants import FAKE_1_ERRATA_ID
from robottelo.constants import FAKE_2_CUSTOM_PACKAGE
from robottelo.constants import FAKE_2_CUSTOM_PACKAGE_NAME
from robottelo.constants import PRDS
from robottelo.constants import REPOS
from robottelo.constants import REPOSET
from robottelo.constants.repos import FAKE_1_YUM_REPO
from robottelo.decorators import skip_if_not_set
from robottelo.test import CLITestCase
from robottelo.vm import VirtualMachine


@pytest.mark.run_in_one_thread
class KatelloAgentTestCase(CLITestCase):
    """Host tests, which require VM with installed katello-agent."""

    org = None
    env = None
    content_view = None
    activation_key = None

    @classmethod
    @pytest.mark.libvirt_content_host
    @skip_if_not_set('clients', 'fake_manifest')
    def setUpClass(cls):
        """Create Org, Lifecycle Environment, Content View, Activation key"""
        super().setUpClass()
        # Create new org, environment, CV and activation key
        KatelloAgentTestCase.org = make_org()
        KatelloAgentTestCase.env = make_lifecycle_environment(
            {'organization-id': KatelloAgentTestCase.org['id']}
        )
        KatelloAgentTestCase.content_view = make_content_view(
            {'organization-id': KatelloAgentTestCase.org['id']}
        )
        KatelloAgentTestCase.activation_key = make_activation_key(
            {
                'lifecycle-environment-id': KatelloAgentTestCase.env['id'],
                'organization-id': KatelloAgentTestCase.org['id'],
            }
        )
        # Add subscription to Satellite Tools repo to activation key
        setup_org_for_a_rh_repo(
            {
                'product': PRDS['rhel'],
                'repository-set': REPOSET['rhst7'],
                'repository': REPOS['rhst7']['name'],
                'organization-id': KatelloAgentTestCase.org['id'],
                'content-view-id': KatelloAgentTestCase.content_view['id'],
                'lifecycle-environment-id': KatelloAgentTestCase.env['id'],
                'activationkey-id': KatelloAgentTestCase.activation_key['id'],
            }
        )
        # Create custom repo, add subscription to activation key
        setup_org_for_a_custom_repo(
            {
                'url': FAKE_1_YUM_REPO,
                'organization-id': KatelloAgentTestCase.org['id'],
                'content-view-id': KatelloAgentTestCase.content_view['id'],
                'lifecycle-environment-id': KatelloAgentTestCase.env['id'],
                'activationkey-id': KatelloAgentTestCase.activation_key['id'],
            }
        )

    def setUp(self):
        """Create VM, subscribe it to satellite-tools repo, install katello-ca
        and katello-agent packages

        """
        super().setUp()
        # Create VM and register content host
        self.client = VirtualMachine(distro=DISTRO_RHEL7)
        self.client.create()
        self.addCleanup(vm_cleanup, self.client)
        self.client.install_katello_ca()
        # Register content host, install katello-agent
        self.client.register_contenthost(
            KatelloAgentTestCase.org['label'], KatelloAgentTestCase.activation_key['name']
        )
        assert self.client.subscribed
        self.host = Host.info({'name': self.client.hostname})
        self.client.enable_repo(REPOS['rhst7']['id'])
        self.client.install_katello_agent()

    @pytest.mark.tier3
    def test_positive_get_errata_info(self):
        """Get errata info

        :id: afb5ab34-1703-49dc-8ddc-5e032c1b86d7

        :expectedresults: Errata info was displayed

        :CaseLevel: System
        """
        self.client.run(f'yum install -y {FAKE_1_CUSTOM_PACKAGE}')
        result = Host.errata_info({'host-id': self.host['id'], 'id': FAKE_1_ERRATA_ID})
        assert result[0]['errata-id'] == FAKE_1_ERRATA_ID
        assert FAKE_2_CUSTOM_PACKAGE in result[0]['packages']

    @pytest.mark.tier3
    @pytest.mark.upgrade
    def test_positive_apply_errata(self):
        """Apply errata to a host

        :id: 8d0e5c93-f9fd-4ec0-9a61-aa93082a30c5

        :expectedresults: Errata is scheduled for installation

        :CaseLevel: System
        """
        self.client.run(f'yum install -y {FAKE_1_CUSTOM_PACKAGE}')
        Host.errata_apply({'errata-ids': FAKE_1_ERRATA_ID, 'host-id': self.host['id']})

    @pytest.mark.tier3
    def test_positive_apply_security_erratum(self):
        """Apply security erratum to a host

        :id: 4d1095c8-d354-42ac-af44-adf6dbb46deb

        :expectedresults: erratum is recognized by the
            `yum update --security` command on client

        :CaseLevel: System

        :BZ: 1420671, 1740790
        """
        self.client.download_install_rpm(FAKE_1_YUM_REPO, FAKE_2_CUSTOM_PACKAGE)
        # Check the system is up to date
        result = self.client.run('yum update --security | grep "No packages needed for security"')
        assert result.return_code == 0
        before_downgrade = int(time.time())
        # Downgrade walrus package
        self.client.run(f'yum downgrade -y {FAKE_2_CUSTOM_PACKAGE_NAME}')
        # Wait for errata applicability cache is counted
        wait_for_errata_applicability_task(int(self.host['id']), before_downgrade)
        # Check that host has applicable errata
        host_errata = Host.errata_list({'host-id': self.host['id']})
        assert host_errata[0]['erratum-id'] == FAKE_1_ERRATA_ID
        assert host_errata[0]['installable'] == 'true'
        # Check the erratum becomes available
        result = self.client.run(
            'yum update --assumeno --security | grep "No packages needed for security"'
        )
        assert result.return_code == 1

    @pytest.mark.tier3
    @pytest.mark.upgrade
    def test_positive_install_package(self):
        """Install a package to a host remotely

        :id: b1009bba-0c7e-4b00-8ac4-256e5cfe4a78

        :expectedresults: Package was successfully installed

        :CaseLevel: System
        """
        Host.package_install({'host-id': self.host['id'], 'packages': FAKE_0_CUSTOM_PACKAGE_NAME})
        result = self.client.run(f'rpm -q {FAKE_0_CUSTOM_PACKAGE_NAME}')
        assert result.return_code == 0

    @pytest.mark.tier3
    def test_positive_remove_package(self):
        """Remove a package from a host remotely

        :id: 573dec11-8f14-411f-9e41-84426b0f23b5

        :expectedresults: Package was successfully removed

        :CaseLevel: System
        """
        self.client.run(f'yum install -y {FAKE_1_CUSTOM_PACKAGE}')
        Host.package_remove({'host-id': self.host['id'], 'packages': FAKE_1_CUSTOM_PACKAGE_NAME})
        result = self.client.run(f'rpm -q {FAKE_1_CUSTOM_PACKAGE_NAME}')
        assert result.return_code != 0

    @pytest.mark.tier3
    def test_positive_upgrade_package(self):
        """Upgrade a host package remotely

        :id: ad751c63-7175-40ae-8bc4-800462cd9c29

        :expectedresults: Package was successfully upgraded

        :CaseLevel: System
        """
        self.client.run(f'yum install -y {FAKE_1_CUSTOM_PACKAGE}')
        Host.package_upgrade({'host-id': self.host['id'], 'packages': FAKE_1_CUSTOM_PACKAGE_NAME})
        result = self.client.run(f'rpm -q {FAKE_2_CUSTOM_PACKAGE}')
        assert result.return_code == 0

    @pytest.mark.tier3
    def test_positive_upgrade_packages_all(self):
        """Upgrade all the host packages remotely

        :id: 003101c7-bb95-4e51-a598-57977b2858a9

        :expectedresults: Packages (at least 1 with newer version available)
            were successfully upgraded

        :CaseLevel: System
        """
        self.client.run(f'yum install -y {FAKE_1_CUSTOM_PACKAGE}')
        Host.package_upgrade_all({'host-id': self.host['id']})
        result = self.client.run(f'rpm -q {FAKE_2_CUSTOM_PACKAGE}')
        assert result.return_code == 0

    @pytest.mark.tier3
    @pytest.mark.upgrade
    def test_positive_install_and_remove_package_group(self):
        """Install and remove a package group to a host remotely

        :id: ded20a89-cfd9-48d5-8829-739b1a4d4042

        :expectedresults: Package group was successfully installed
            and removed

        :CaseLevel: System
        """
        hammer_args = {'groups': FAKE_0_CUSTOM_PACKAGE_GROUP_NAME, 'host-id': self.host['id']}
        Host.package_group_install(hammer_args)
        for package in FAKE_0_CUSTOM_PACKAGE_GROUP:
            result = self.client.run(f'rpm -q {package}')
            assert result.return_code == 0
        Host.package_group_remove(hammer_args)
        for package in FAKE_0_CUSTOM_PACKAGE_GROUP:
            result = self.client.run(f'rpm -q {package}')
            assert result.return_code != 0

    @pytest.mark.tier3
    def test_negative_unregister_and_pull_content(self):
        """Attempt to retrieve content after host has been unregistered from
        Satellite

        :id: de0d0d91-b1e1-4f0e-8a41-c27df4d6b6fd

        :expectedresults: Host can no longer retrieve content from satellite

        :CaseLevel: System
        """
        result = self.client.run('subscription-manager unregister')
        assert result.return_code == 0
        result = self.client.run(f'yum install -y {FAKE_1_CUSTOM_PACKAGE}')
        assert result.return_code != 0

    @pytest.mark.tier3
    @pytest.mark.libvirt_content_host
    @pytest.mark.upgrade
    def test_positive_register_host_ak_with_host_collection(self):
        """Attempt to register a host using activation key with host collection

        :id: 7daf4e40-3fa6-42af-b3f7-1ca1a5c9bfeb

        :BZ: 1385814

        :expectedresults: Host successfully registered and listed in host
            collection

        :CaseLevel: System
        """
        # create a new activation key
        activation_key = make_activation_key(
            {
                'lifecycle-environment-id': self.env['id'],
                'organization-id': self.org['id'],
                'content-view-id': self.content_view['id'],
            }
        )
        hc = make_host_collection({'organization-id': self.org['id']})
        ActivationKey.add_host_collection(
            {
                'id': activation_key['id'],
                'organization-id': self.org['id'],
                'host-collection-id': hc['id'],
            }
        )
        # add the registered instance host to collection
        HostCollection.add_host(
            {'id': hc['id'], 'organization-id': self.org['id'], 'host-ids': self.host['id']}
        )
        with VirtualMachine() as client:
            client.create()
            client.install_katello_ca()
            # register the client host with the current activation key
            client.register_contenthost(self.org['name'], activation_key=activation_key['name'])
            assert client.subscribed
            # note: when registering the host, it should be automatically added
            # to the host collection
            client_host = Host.info({'name': client.hostname})
            hosts = HostCollection.hosts({'id': hc['id'], 'organization-id': self.org['id']})
            assert len(hosts) == 2
            expected_hosts_ids = {self.host['id'], client_host['id']}
            hosts_ids = {host['id'] for host in hosts}
            assert hosts_ids == expected_hosts_ids
