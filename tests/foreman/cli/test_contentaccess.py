"""Test for Content Access (Golden Ticket) CLI

:Requirement: Content Access

:CaseLevel: Acceptance

:CaseComponent: Hosts-Content

:Assignee: swadeley

:TestType: Functional

:Upstream: No
"""
import time

import pytest

from robottelo import manifests
from robottelo import ssh
from robottelo.cli.contentview import ContentView
from robottelo.cli.factory import make_content_view
from robottelo.cli.factory import make_org
from robottelo.cli.factory import setup_cdn_and_custom_repositories
from robottelo.cli.factory import setup_virtual_machine
from robottelo.cli.host import Host
from robottelo.cli.package import Package
from robottelo.constants import DISTRO_RHEL7
from robottelo.constants import ENVIRONMENT
from robottelo.constants import PRDS
from robottelo.constants import REAL_RHEL7_0_0_PACKAGE
from robottelo.constants import REAL_RHEL7_0_0_PACKAGE_NAME
from robottelo.constants import REAL_RHEL7_0_1_PACKAGE_FILENAME
from robottelo.constants import REAL_RHEL7_0_ERRATA_ID
from robottelo.constants import REPOS
from robottelo.constants import REPOSET
from robottelo.decorators import skip_if_not_set
from robottelo.test import CLITestCase
from robottelo.vm import VirtualMachine


@pytest.mark.libvirt_content_host
@pytest.mark.run_in_one_thread
class ContentAccessTestCase(CLITestCase):
    """Content Access CLI tests."""

    @classmethod
    @skip_if_not_set('clients', 'fake_manifest')
    def setUpClass(cls):
        """Setup must ensure there is an Org with Golden Ticket enabled.


        Option 1) SQL::

            UPDATE
                 cp_owner
            SET
                 content_access_mode = 'org_environment',
                 content_access_mode_list='entitlement,org_environment'
            WHERE account='{org.label}';

        Option 2) manifest::

            Change manifest file as it looks like:

                Consumer:
                    Name: ExampleCorp
                    UUID: c319a1d8-4b30-44cd-b2cf-2ccba4b9a8db
                    Content Access Mode: org_environment
                    Type: satellite

        :steps:

            1. Create a new organization.
            2. Use either option 1 or option 2 (described above) to activate
               the Golden Ticket.
            3. Create a Product and CV for org.
            4. Add a repository pointing to a real repo which requires a
               RedHat subscription to access.
            5. Create Content Host and assign that gated repos to it.
            6. Sync the gated repository.
        """
        super().setUpClass()
        # Create Organization
        cls.org = make_org()
        # upload organization manifest with org environment access enabled
        cls.manifest = manifests.clone(org_environment_access=True)
        manifests.upload_manifest_locked(
            cls.org['id'], cls.manifest, interface=manifests.INTERFACE_CLI
        )
        # Create repositories
        cls.repos = [
            # Red Hat Satellite Tools from CDN
            {
                'product': PRDS['rhel'],
                'repository-set': REPOSET['rhst7'],
                'repository': REPOS['rhst7']['name'],
                'repository-id': REPOS['rhst7']['id'],
                'releasever': REPOS['rhel7']['releasever'],
                'arch': REPOS['rhel7']['arch'],
                'cdn': True,
            },
        ]
        cls.repos_info = setup_cdn_and_custom_repositories(cls.org['id'], cls.repos)
        # Create a content view
        content_view = make_content_view({'organization-id': cls.org['id']})
        # Add repositories to content view
        ContentView.add_repository(
            {
                'id': content_view['id'],
                'organization-id': cls.org['id'],
                'repository-id': cls.repos_info[1][0]['id'],
            }
        )
        # Publish the content view
        ContentView.publish({'id': content_view['id']})
        cls.content_view = ContentView.info({'id': content_view['id']})

    def _setup_virtual_machine(self, vm):
        """Make the initial virtual machine setup

        :param VirtualMachine vm: The virtual machine setup
        """
        setup_virtual_machine(
            vm,
            self.org['label'],
            rh_repos_id=[repo['repository-id'] for repo in self.repos if repo['cdn']],
            repos_label=self.repos_info[1][0]['label'],
            lce=ENVIRONMENT,
            patch_os_release_distro=DISTRO_RHEL7,
            install_katello_agent=True,
        )

    @pytest.mark.tier2
    def test_positive_list_installable_updates(self):
        """Ensure packages applicability is functioning properly.

        :id: 4feb692c-165b-4f96-bb97-c8447bd2cf6e

        :steps:

            1. Setup a content host with registration to unrestricted org
            2. Install a packages that has updates
            3. Run `hammer package list` specifying option
               packages-restrict-applicable="true".

        :CaseAutomation: Automated

        :expectedresults:
            1. Update package is available independent of subscription because
               Golden Ticket is enabled.

        :BZ: 1344049, 1498158

        :CaseImportance: Critical
        """
        with VirtualMachine(distro=DISTRO_RHEL7) as vm:
            self._setup_virtual_machine(vm)
            # install the packages that require updates
            result = vm.run(f'yum install -y {REAL_RHEL7_0_0_PACKAGE}')
            self.assertEqual(result.return_code, 0)
            result = vm.run(f'rpm -q {REAL_RHEL7_0_0_PACKAGE}')
            self.assertEqual(result.return_code, 0)
            for _ in range(30):
                applicable_packages = Package.list(
                    {
                        'host': vm.hostname,
                        'packages-restrict-applicable': 'true',
                        'search': f'name={REAL_RHEL7_0_0_PACKAGE_NAME}',
                    }
                )
                if applicable_packages:
                    break
                time.sleep(10)
            self.assertGreater(len(applicable_packages), 0)
            self.assertIn(
                REAL_RHEL7_0_1_PACKAGE_FILENAME,
                [package['filename'] for package in applicable_packages],
            )

    @pytest.mark.tier2
    @pytest.mark.upgrade
    def test_positive_erratum_installable(self):
        """Ensure erratum applicability is showing properly, without attaching
        any subscription.

        :id: e8dc52b9-884b-40d7-9244-680b5a736cf7

        :CaseAutomation: Automated

        :steps:
            1. register a host to unrestricted org with Library
            2. install a package, that will need errata to be applied
            3. list the host applicable errata with searching the required
               errata id

        :expectedresults: errata listed successfuly and is installable

        :BZ: 1344049, 1498158

        :CaseImportance: Critical
        """
        with VirtualMachine(distro=DISTRO_RHEL7) as vm:
            self._setup_virtual_machine(vm)
            # install the packages that require updates
            result = vm.run(f'yum install -y {REAL_RHEL7_0_0_PACKAGE}')
            self.assertEqual(result.return_code, 0)
            result = vm.run(f'rpm -q {REAL_RHEL7_0_0_PACKAGE}')
            self.assertEqual(result.return_code, 0)
            # check that package errata is applicable
            for _ in range(30):
                erratum = Host.errata_list(
                    {'host': vm.hostname, 'search': f'id = {REAL_RHEL7_0_ERRATA_ID}'}
                )
                if erratum:
                    break
                time.sleep(10)
            self.assertEqual(len(erratum), 1)
            self.assertEqual(erratum[0]['installable'], 'true')

    @pytest.mark.tier2
    def test_negative_rct_not_shows_golden_ticket_enabled(self):
        """Assert restricted manifest has no Golden Ticket enabled .

        :id: 754c1be7-468e-4795-bcf9-258a38f3418b

        :steps:

            1. Run `rct cat-manifest /tmp/restricted_manifest.zip`.

        :CaseAutomation: Automated

        :expectedresults:
            1. Assert `Content Access Mode: org_environment` is not present.

        :CaseImportance: High
        """
        org = make_org()
        # upload organization manifest with org environment access enabled
        manifest = manifests.clone()
        manifests.upload_manifest_locked(org['id'], manifest, interface=manifests.INTERFACE_CLI)
        result = ssh.command(f'rct cat-manifest {manifest.filename}')
        self.assertEqual(result.return_code, 0)
        self.assertNotIn('Content Access Mode: org_environment', '\n'.join(result.stdout))

    @pytest.mark.tier2
    @pytest.mark.upgrade
    def test_positive_rct_shows_golden_ticket_enabled(self):
        """Assert unrestricted manifest has Golden Ticket enabled .

        :id: 0c6e2f88-1a86-4417-9248-d7bd20584197

        :steps:

            1. Run `rct cat-manifest /tmp/unrestricted_manifest.zip`.

        :CaseAutomation: Automated

        :expectedresults:
            1. Assert `Content Access Mode: org_environment` is present.

        :CaseImportance: Medium
        """
        result = ssh.command(f'rct cat-manifest {self.manifest.filename}')
        self.assertEqual(result.return_code, 0)
        self.assertIn('Content Access Mode: org_environment', '\n'.join(result.stdout))
