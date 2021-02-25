"""Tests for the Incremental Update feature

:Requirement: Inc Updates

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Hosts-Content

:Assignee: swadeley

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from datetime import date
from datetime import datetime
from datetime import timedelta

import pytest
from fauxfactory import gen_alpha
from nailgun import entities
from nailgun import entity_mixins

from robottelo import manifests
from robottelo.api.utils import call_entity_method_with_timeout
from robottelo.api.utils import enable_rhrepo_and_fetchid
from robottelo.api.utils import promote
from robottelo.api.utils import upload_manifest
from robottelo.api.utils import wait_for_tasks
from robottelo.cleanup import vm_cleanup
from robottelo.cli.contentview import ContentView as ContentViewCLI
from robottelo.constants import DEFAULT_ARCHITECTURE
from robottelo.constants import DEFAULT_RELEASE_VERSION
from robottelo.constants import DEFAULT_SUBSCRIPTION_NAME
from robottelo.constants import DISTRO_RHEL6
from robottelo.constants import PRDS
from robottelo.constants import REAL_0_RH_PACKAGE
from robottelo.constants import REPOS
from robottelo.constants import REPOSET
from robottelo.decorators import skip_if_not_set
from robottelo.test import TestCase
from robottelo.vm import VirtualMachine


@pytest.mark.libvirt_content_host
@pytest.mark.run_in_one_thread
class IncrementalUpdateTestCase(TestCase):
    """Tests for the Incremental Update feature"""

    @classmethod
    @skip_if_not_set('clients')
    def setUpClass(cls):
        """Creates the pre-requisites for the Incremental updates that used in
        all test"""
        super().setUpClass()
        # Create a new Organization
        cls.org = entities.Organization(name=gen_alpha()).create()

        # Create two lifecycle environments - DEV, QE
        cls.dev_lce = entities.LifecycleEnvironment(name='DEV', organization=cls.org).create()
        cls.qe_lce = entities.LifecycleEnvironment(
            name='QE', prior=cls.dev_lce, organization=cls.org
        ).create()

        # Upload manifest
        with manifests.clone() as manifest:
            upload_manifest(cls.org.id, manifest.content)

        # Enable repositories - RHE Virtualization Agents and rhel6 sat6tools
        rhva_6_repo_id = enable_rhrepo_and_fetchid(
            basearch=DEFAULT_ARCHITECTURE,
            org_id=cls.org.id,
            product=PRDS['rhel'],
            repo=REPOS['rhva6']['name'],
            reposet=REPOSET['rhva6'],
            releasever=DEFAULT_RELEASE_VERSION,
        )
        rhel6_sat6tools_repo_id = enable_rhrepo_and_fetchid(
            basearch=DEFAULT_ARCHITECTURE,
            org_id=cls.org.id,
            product=PRDS['rhel'],
            repo=REPOS['rhst6']['name'],
            reposet=REPOSET['rhst6'],
            releasever=None,
        )

        # Read the repositories
        cls.rhva_6_repo = entities.Repository(id=rhva_6_repo_id).read()
        cls.rhel6_sat6tools_repo = entities.Repository(id=rhel6_sat6tools_repo_id).read()

        # Sync the enabled repositories
        try:
            cls.old_task_timeout = entity_mixins.TASK_TIMEOUT
            # Update timeout to 15 minutes to finish sync
            entity_mixins.TASK_TIMEOUT = 900
            for repo in [cls.rhva_6_repo, cls.rhel6_sat6tools_repo]:
                assert repo.sync()['result'] == 'success'
        finally:
            entity_mixins.TASK_TIMEOUT = cls.old_task_timeout

    def setUp(self):
        """Creates the pre-requisites for the Incremental updates that used per
        each test"""
        super().setUp()
        # Create content view that will be used filtered erratas
        self.rhel_6_partial_cv = entities.ContentView(
            organization=self.org,
            name=gen_alpha(),
            repository=[self.rhva_6_repo, self.rhel6_sat6tools_repo],
        ).create()

        # Create a content view filter to filter out errata
        rhel_6_partial_cvf = entities.ErratumContentViewFilter(
            content_view=self.rhel_6_partial_cv,
            type='erratum',
            name='rhel_6_partial_cv_filter',
            repository=[self.rhva_6_repo],
        ).create()

        # Create a content view filter rule - filtering out errata in the last
        # 365 days
        start_date = (date.today() - timedelta(days=365)).strftime('%Y-%m-%d')
        entities.ContentViewFilterRule(
            content_view_filter=rhel_6_partial_cvf,
            types=['security', 'enhancement', 'bugfix'],
            start_date=start_date,
            end_date=date.today().strftime('%Y-%m-%d'),
        ).create()

        # Publish content view and re-read it

        self.rhel_6_partial_cv.publish()
        self.rhel_6_partial_cv = self.rhel_6_partial_cv.read()

        # Promote content view to 'DEV' and 'QE'
        assert len(self.rhel_6_partial_cv.version) == 1
        for env in (self.dev_lce, self.qe_lce):
            promote(self.rhel_6_partial_cv.version[0], env.id)

        # Create host collection
        self.rhel_6_partial_hc = entities.HostCollection(
            organization=self.org, name=gen_alpha(), max_hosts=5
        ).create()

        # Create activation key for content view
        kwargs = {'organization': self.org, 'environment': self.qe_lce.id}
        rhel_6_partial_ak = entities.ActivationKey(
            name=gen_alpha(),
            content_view=self.rhel_6_partial_cv,
            host_collection=[self.rhel_6_partial_hc],
            **kwargs,
        ).create()

        # Fetch available subscriptions
        subs = entities.Subscription(organization=self.org).search()
        assert len(subs) > 0

        # Add default subscription to activation key
        sub_found = False
        for sub in subs:
            if sub.name == DEFAULT_SUBSCRIPTION_NAME:
                rhel_6_partial_ak.add_subscriptions(data={'subscription_id': sub.id})
                sub_found = True
        assert sub_found

        # Enable product content in activation key
        rhel_6_partial_ak.content_override(
            data={'content_overrides': [{'content_label': REPOS['rhst6']['id'], 'value': '1'}]}
        )

        # Create client machine and register it to satellite with
        # rhel_6_partial_ak
        self.vm = VirtualMachine(distro=DISTRO_RHEL6, tag='incupdate')
        self.addCleanup(vm_cleanup, self.vm)
        self.setup_vm(self.vm, rhel_6_partial_ak.name, self.org.label)
        self.vm.enable_repo(REPOS['rhva6']['id'])
        timestamp = datetime.utcnow()
        self.vm.run(f'yum install -y {REAL_0_RH_PACKAGE}')

        # Find the content host and ensure that tasks started by package
        # installation has finished
        host = entities.Host().search(query={'search': f'name={self.vm.hostname}'})
        wait_for_tasks(
            search_query='label = Actions::Katello::Host::UploadPackageProfile'
            ' and resource_id = {}'
            ' and started_at >= "{}"'.format(host[0].id, timestamp)
        )
        # Force host to generate or refresh errata applicability
        call_entity_method_with_timeout(host[0].errata_applicability, timeout=600)

    @staticmethod
    def setup_vm(client, act_key, org_name):
        """Creates the vm and registers it to the satellite"""
        client.create()
        client.install_katello_ca()

        # Register content host, install katello-agent
        client.register_contenthost(org_name, act_key, releasever=DEFAULT_RELEASE_VERSION)
        assert client.subscribed
        client.install_katello_agent()
        client.run('katello-package-upload')

    @staticmethod
    def get_applicable_errata(repo):
        """Retrieves applicable errata for the given repo"""
        return entities.Errata(repository=repo).search(query={'errata_restrict_applicable': True})

    @pytest.mark.tier4
    @pytest.mark.upgrade
    def test_positive_noapply_api(self):
        """Check if api incremental update can be done without
        actually applying it

        :id: 481c5ff2-801f-4eff-b1e0-95ea5bb37f95

        :Setup:  The prerequisites are already covered in the setUpClass() but
            for easy debug, get the content view id, Repository id and
            Lifecycle environment id using hammer and plug these statements on
            the top of the test. For example::

                self.rhel_6_partial_cv = ContentView(id=38).read()
                self.rhva_6_repo = Repository(id=164).read()
                self.qe_lce = LifecycleEnvironment(id=46).read()

        :expectedresults: Incremental update completed with no errors and
            Content view has a newer version

        :CaseLevel: System
        """
        # Get the content view versions and use the recent one.  API always
        # returns the versions in ascending order so it is safe to assume the
        # last one in the list is the recent
        cv_versions = self.rhel_6_partial_cv.version

        # Get the applicable errata
        errata_list = self.get_applicable_errata(self.rhva_6_repo)
        self.assertGreater(len(errata_list), 0)

        # Apply incremental update using the first applicable errata
        entities.ContentViewVersion().incremental_update(
            data={
                'content_view_version_environments': [
                    {
                        'content_view_version_id': cv_versions[-1].id,
                        'environment_ids': [self.qe_lce.id],
                    }
                ],
                'add_content': {'errata_ids': [errata_list[0].id]},
            }
        )

        # Re-read the content view to get the latest versions
        self.rhel_6_partial_cv = self.rhel_6_partial_cv.read()
        self.assertGreater(len(self.rhel_6_partial_cv.version), len(cv_versions))

    @pytest.mark.tier4
    @pytest.mark.upgrade
    def test_positive_noapply_cli(self):
        """Check if cli incremental update can be done without
        actually applying it

        :id: f25b0919-74cb-4e2c-829e-482558990b3c

        :expectedresults: Incremental update completed with no errors and
            Content view has a newer version

        :CaseLevel: System
        """
        # Get the content view versions and use the recent one.  API always
        # returns the versions in ascending order so it is safe to assume the
        # last one in the list is the recent

        cv_versions = self.rhel_6_partial_cv.version

        # Get the applicable errata
        errata_list = self.get_applicable_errata(self.rhva_6_repo)
        self.assertGreater(len(errata_list), 0)

        # Apply incremental update using the first applicable errata
        ContentViewCLI.version_incremental_update(
            {
                'content-view-version-id': cv_versions[-1].id,
                'lifecycle-environment-ids': self.qe_lce.id,
                'errata-ids': errata_list[0].id,
            }
        )

        # Re-read the content view to get the latest versions
        self.rhel_6_partial_cv = self.rhel_6_partial_cv.read()
        self.assertGreater(len(self.rhel_6_partial_cv.version), len(cv_versions))
