# -*- encoding: utf-8 -*-
"""Test for Content Access (Golden Ticket) API

:Requirement: Content Access

:CaseLevel: Acceptance

:CaseComponent: API

:TestType: Functional

:CaseImportance: high

:Upstream: No
"""
from nailgun import entities

from robottelo import manifests
from robottelo.api.utils import call_entity_method_with_timeout
from robottelo.constants import (
    DISTRO_RHEL7,
    ENVIRONMENT,
    PRDS,
    REPOS,
    REPOSET,
)
from robottelo.cli.factory import setup_cdn_and_custom_repositories
from robottelo.config import settings
from robottelo.decorators import (
    run_in_one_thread,
    run_only_on,
    skip_if_not_set,
    tier2,
)
from robottelo.test import APITestCase
from robottelo.vm import VirtualMachine


@run_in_one_thread
class ContentAccessTestCase(APITestCase):
    """Content Access API tests."""

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
            6. Create Host with no attached subscriptions.
            7. Sync the gated repository.

        """
        super(ContentAccessTestCase, cls).setUpClass()
        # Create Organization
        cls.org = entities.Organization().create()
        # upload organization manifest with org environment access enabled
        manifests.upload_manifest_locked(
            cls.org.id,
            manifests.clone(org_environment_access=True)
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
        cls.repos_info = setup_cdn_and_custom_repositories(
            cls.org.id, cls.repos)
        # Create a content view
        content_view = entities.ContentView(
            organization=cls.org,
            repository=[entities.Repository(id=repo_info['id'])
                        for repo_info in cls.repos_info],
        ).create()
        # Publish the content view
        call_entity_method_with_timeout(content_view.publish, timeout=1500)
        cls.content_view = content_view.read()

    @run_only_on('sat')
    @tier2
    def test_positive_list_hosts_applicable(self):
        """Request `errata/hosts_applicable` and assert the host with no
        attached subscriptions is present.

        :id: 68ed5b10-7a45-4f2d-93ed-cffa737211d5

        :steps:

            1. Request errata/hosts_applicable for organization created on
               setUp.

        :CaseAutomation: automated

        :expectedresults:
            1. Assert the host with no attached subscription is listed to have
               access to errata content.

        :CaseImportance: Critical
        """
        with VirtualMachine(distro=DISTRO_RHEL7) as vm:
            vm.create()
            vm.install_katello_ca()
            vm.register_contenthost(self.org.label, lce=ENVIRONMENT)
            self.assertTrue(vm.subscribed)
            vm.patch_os_release_version(distro=DISTRO_RHEL7)
            # trigger subscription-manager repos to auto enable repositories
            result = vm.run('subscription-manager repos')
            self.assertEqual(result.return_code, 0)
            # at this stage all repositories should be enabled automatically
            vm.install_katello_agent()
            host = entities.Host(
                name=vm.hostname, organization=self.org).search()[0].read()
            # force host to generate errata applicability
            host.errata_applicability()
            erratum = host.errata()['results']
            self.assertGreater(len(erratum), 0)
