# -*- encoding: utf-8 -*-
""""Test for Content Access (Golden Ticket) CLI

:Requirement: Content Access

:CaseLevel: Acceptance

:CaseComponent: Hosts-Content

:TestType: Functional

:CaseImportance: high

:Upstream: No
"""
import time

from robottelo import manifests
from robottelo import ssh
from robottelo.cli.contentview import ContentView
from robottelo.cli.factory import (
    make_content_view,
    make_org,
    setup_cdn_and_custom_repositories,
    setup_virtual_machine,
)
from robottelo.cli.host import Host
from robottelo.cli.package import Package
from robottelo.config import settings
from robottelo.constants import (
    DISTRO_RHEL7,
    ENVIRONMENT,
    REAL_RHEL7_0_0_PACKAGE,
    REAL_RHEL7_0_0_PACKAGE_NAME,
    REAL_RHEL7_0_1_PACKAGE_FILENAME,
    REAL_RHEL7_0_ERRATA_ID,
    REPOS,
    REPOSET,
    PRDS,
)
from robottelo.decorators import (
    run_in_one_thread,
    skip_if_not_set,
    tier2,
    upgrade
)
from robottelo.test import CLITestCase
from robottelo.vm import VirtualMachine


@run_in_one_thread
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
        super(ContentAccessTestCase, cls).setUpClass()
        # Create Organization
        cls.org = make_org()
        # upload organization manifest with org environment access enabled
        cls.manifest = manifests.clone(org_environment_access=True)
        manifests.upload_manifest_locked(
            cls.org['id'],
            cls.manifest,
            interface=manifests.INTERFACE_CLI
        )
        # Create repositories
        cls.repos = [
            # Red Hat Enterprise Linux 7
            {
                'product': PRDS['rhel'],
                'repository-set': REPOSET['rhel7'],
                'repository': REPOS['rhel7']['name'],
                'repository-id': REPOS['rhel7']['id'],
                'releasever': REPOS['rhel7']['releasever'],
                'arch': REPOS['rhel7']['arch'],
                'cdn': True,
            },
            # Red Hat Satellite Tools
            {
                'product': PRDS['rhel'],
                'repository-set': REPOSET['rhst7'],
                'repository': REPOS['rhst7']['name'],
                'repository-id': REPOS['rhst7']['id'],
                'url': settings.sattools_repo['rhel7'],
                'cdn': bool(
                    settings.cdn or not settings.sattools_repo['rhel7']),
            },
        ]
        cls.custom_product, cls.repos_info = setup_cdn_and_custom_repositories(
            cls.org['id'], cls.repos)
        # Create a content view
        content_view = make_content_view({u'organization-id': cls.org['id']})
        # Add repositories to content view
        for repo_info in cls.repos_info:
            ContentView.add_repository({
                u'id': content_view['id'],
                u'organization-id': cls.org['id'],
                u'repository-id': repo_info['id'],
            })
        # Publish the content view
        ContentView.publish({u'id': content_view['id']})
        cls.content_view = ContentView.info({u'id': content_view['id']})

    def _setup_virtual_machine(self, vm):
        """Make the initial virtual machine setup

        :param VirtualMachine vm: The virtual machine setup
        """
        setup_virtual_machine(
            vm,
            self.org['label'],
            rh_repos_id=[
                repo['repository-id'] for repo in self.repos if repo['cdn']
            ],
            product_label=self.custom_product['label'],
            repos_label=[
                repo['label'] for repo in self.repos_info
                if repo['red-hat-repository'] == 'no'
            ],
            lce=ENVIRONMENT,
            patch_os_release_distro=DISTRO_RHEL7,
            install_katello_agent=True,
        )

    @tier2
    def test_positive_list_installable_updates(self):
        """Ensure packages applicability is functioning properly.

        :id: 4feb692c-165b-4f96-bb97-c8447bd2cf6e

        :steps:

            1. Setup a content host with registration to unrestricted org
            2. Install a packages that has updates
            3. Run `hammer package list` specifying option
               packages-restrict-applicable="true".

        :CaseAutomation: automated

        :expectedresults:
            1. Update package is available independent of subscription because
               Golden Ticket is enabled.

        :BZ: 1344049, 1498158

        :CaseImportance: Critical
        """
        with VirtualMachine(distro=DISTRO_RHEL7) as vm:
            self._setup_virtual_machine(vm)
            # install a the packages that has updates
            result = vm.run(
                'yum install -y {0}'.format(REAL_RHEL7_0_0_PACKAGE))
            self.assertEqual(result.return_code, 0)
            result = vm.run('rpm -q {0}'.format(REAL_RHEL7_0_0_PACKAGE))
            self.assertEqual(result.return_code, 0)
            for _ in range(30):
                applicable_packages = Package.list({
                    'host': vm.hostname,
                    'packages-restrict-applicable': 'true',
                    'search': 'name={0}'.format(REAL_RHEL7_0_0_PACKAGE_NAME)
                })
                if applicable_packages:
                    break
                time.sleep(10)
            self.assertGreater(len(applicable_packages), 0)
            self.assertIn(
                REAL_RHEL7_0_1_PACKAGE_FILENAME,
                [package['filename'] for package in applicable_packages]
            )

    @tier2
    @upgrade
    def test_positive_erratum_installable(self):
        """Ensure erratum applicability is showing properly, without attaching
        any subscription.

        :id: e8dc52b9-884b-40d7-9244-680b5a736cf7

        :CaseAutomation: automated

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
            # install a the packages that has updates with errata
            result = vm.run(
                'yum install -y {0}'.format(REAL_RHEL7_0_0_PACKAGE))
            self.assertEqual(result.return_code, 0)
            result = vm.run('rpm -q {0}'.format(REAL_RHEL7_0_0_PACKAGE))
            self.assertEqual(result.return_code, 0)
            # check that package errata is applicable
            for _ in range(30):
                erratum = Host.errata_list({
                    'host': vm.hostname,
                    'search': 'id = {0}'.format(REAL_RHEL7_0_ERRATA_ID)
                })
                if erratum:
                    break
                time.sleep(10)
            self.assertEqual(len(erratum), 1)
            self.assertEqual(erratum[0]['installable'], 'true')

    @tier2
    def test_negative_rct_not_shows_golden_ticket_enabled(self):
        """Assert restricted manifest has no Golden Ticket enabled .

        :id: 754c1be7-468e-4795-bcf9-258a38f3418b

        :steps:

            1. Run `rct cat-manifest /tmp/restricted_manifest.zip`.

        :CaseAutomation: automated

        :expectedresults:
            1. Assert `Content Access Mode: org_environment` is not present.

        :CaseImportance: High
        """
        org = make_org()
        # upload organization manifest with org environment access enabled
        manifest = manifests.clone()
        manifests.upload_manifest_locked(
            org['id'],
            manifest,
            interface=manifests.INTERFACE_CLI
        )
        result = ssh.command(
            'rct cat-manifest {0}'.format(manifest.filename))
        self.assertEqual(result.return_code, 0)
        self.assertNotIn(
            'Content Access Mode: org_environment',
            '\n'.join(result.stdout)
        )

    @tier2
    @upgrade
    def test_positive_rct_shows_golden_ticket_enabled(self):
        """Assert unrestricted manifest has Golden Ticket enabled .

        :id: 0c6e2f88-1a86-4417-9248-d7bd20584197

        :steps:

            1. Run `rct cat-manifest /tmp/unrestricted_manifest.zip`.

        :CaseAutomation: automated

        :expectedresults:
            1. Assert `Content Access Mode: org_environment` is present.

        :CaseImportance: Medium
        """
        result = ssh.command(
            'rct cat-manifest {0}'.format(self.manifest.filename))
        self.assertEqual(result.return_code, 0)
        self.assertIn(
            'Content Access Mode: org_environment',
            '\n'.join(result.stdout)
        )
