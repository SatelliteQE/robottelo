"""Tests for the Incremental Update feature"""

from datetime import date, timedelta
from fauxfactory import gen_alpha
from nailgun import entity_mixins
from nailgun.entities import (
    ActivationKey, ContentView, ContentViewFilterRule, ContentViewVersion,
    Errata, ErratumContentViewFilter, HostCollection, LifecycleEnvironment,
    Organization, Repository, Subscription, System
)
from robottelo import manifests
from robottelo.api.utils import (
    enable_rhrepo_and_fetchid, promote, upload_manifest
)
from robottelo.cli.contentview import ContentView as ContentViewCLI
from robottelo.constants import PRD_SETS
from robottelo.decorators import run_only_on, skip_if_bug_open
from robottelo.test import TestCase
from robottelo.vm import VirtualMachine


class TestIncrementalUpdate(TestCase):
    """Tests for the Incremental Update feature"""

    @classmethod
    def setUpClass(cls):
        """Creates all the pre-requisites for the Incremental updates test"""
        super(TestIncrementalUpdate, cls).setUpClass()
        # Step 1 - Create a new Organization
        cls.org = Organization(name=gen_alpha()).create()

        # Step 2 - Create two life cycle environments - DEV, QE
        cls.dev_lce = LifecycleEnvironment(
            name='DEV',
            organization=cls.org
        ).create()
        cls.qe_lce = LifecycleEnvironment(
            name='QE',
            prior=cls.dev_lce,
            organization=cls.org
        ).create()

        # Step 3: Upload manifest
        with open(manifests.clone(), 'rb') as manifest:
            upload_manifest(cls.org.id, manifest)

        # Step 4: Enable repositories - 6Server and rhel6 sat6tools
        rhel_66_repo_id = enable_rhrepo_and_fetchid(
            basearch=PRD_SETS['rhel_66']['arch'],
            org_id=cls.org.id,
            product=PRD_SETS['rhel_66']['product'],
            repo=PRD_SETS['rhel_66']['reponame'],
            reposet=PRD_SETS['rhel_66']['reposet'],
            releasever=PRD_SETS['rhel_66']['releasever']
        )
        rhel6_sat6tools_repo_id = enable_rhrepo_and_fetchid(
            basearch=PRD_SETS['rhel6_sat6tools']['arch'],
            org_id=cls.org.id,
            product=PRD_SETS['rhel6_sat6tools']['product'],
            repo=PRD_SETS['rhel6_sat6tools']['reponame'],
            reposet=PRD_SETS['rhel6_sat6tools']['reposet'],
            releasever=PRD_SETS['rhel6_sat6tools']['releasever']
        )

        # Step 5: Read the repositories
        cls.rhel_66_repo = Repository(id=rhel_66_repo_id).read()
        cls.rhel6_sat6tools_repo = Repository(
            id=rhel6_sat6tools_repo_id
        ).read()

        # Step 6: Sync the enabled repositories
        try:
            cls.old_task_timeout = entity_mixins.TASK_TIMEOUT
            # Update timeout to 2 hours to finish sync
            entity_mixins.TASK_TIMEOUT = 7200
            for repo in [cls.rhel_66_repo, cls.rhel6_sat6tools_repo]:
                assert Repository(id=repo.id).sync()['result'] == u'success'
        finally:
            entity_mixins.TASK_TIMEOUT = cls.old_task_timeout

        # Step 7: Create two content views - one will be used with all erratas
        # and another with erratas filtered
        for cv_name in ('rhel_6_cv', 'rhel_6_partial_cv'):
            setattr(cls, cv_name, ContentView(
                organization=cls.org,
                name=cv_name,
                repository=[cls.rhel_66_repo, cls.rhel6_sat6tools_repo]
            ).create())

        # Step 8: Create a content view filter to filter out errata
        rhel_6_partial_cvf = ErratumContentViewFilter(
            content_view=cls.rhel_6_partial_cv,
            type='erratum',
            name='rhel_6_partial_cv_filter',
            repository=[cls.rhel_66_repo]
        ).create()

        # Step 9: Create a content view filter rule - filtering out errata in
        # the last 365 days
        start_date = (date.today() - timedelta(days=365)).strftime('%Y-%m-%d')
        ContentViewFilterRule(
            content_view_filter=rhel_6_partial_cvf,
            types=['security', 'enhancement', 'bugfix'],
            start_date=start_date,
            end_date=date.today().strftime('%Y-%m-%d')
        ).create()

        # Step 10: Publish both the content views and re-read the content views

        # Changing the nailgun timeout time for the rest of the steps as
        # publish/promote of larger repos take more than 5 minutes
        entity_mixins.TASK_TIMEOUT = 3600
        for content_view in (cls.rhel_6_cv, cls.rhel_6_partial_cv):
            content_view.publish()
        cls.rhel_6_cv = cls.rhel_6_cv.read()
        cls.rhel_6_partial_cv = cls.rhel_6_partial_cv.read()

        # Step 11: Promote both content views to 'DEV' and 'QE'
        for content_view in (cls.rhel_6_cv, cls.rhel_6_partial_cv):
            assert len(content_view.version) == 1
            for env in (cls.dev_lce, cls.qe_lce):
                promote(content_view.version[0], env.id)

        # Step 12: Create host collections
        for hc_name in ('rhel_6_hc', 'rhel_6_partial_hc'):
            setattr(
                cls,
                hc_name,
                HostCollection(
                    organization=cls.org, name=hc_name, max_content_hosts=5
                ).create()
            )

        # Step 13: Create activation keys for both content views
        kwargs = {'organization': cls.org, 'environment': cls.qe_lce.id}
        rhel_6_ak = ActivationKey(
            name=u'rhel_6_ak',
            content_view=cls.rhel_6_cv,
            host_collection=[cls.rhel_6_hc],
            **kwargs
        ).create()
        rhel_6_partial_ak = ActivationKey(
            name=u'rhel_6_partial_ak',
            content_view=cls.rhel_6_partial_cv,
            host_collection=[cls.rhel_6_partial_hc],
            **kwargs
        ).create()

        # Step 14: Assign subscriptions to activation keys
        # Fetch available subscriptions
        subs = Subscription(organization=cls.org).search()
        assert len(subs) > 0

        # Add subscriptions to activation key
        sub_found = False
        for sub in subs:
            if sub.read_json()['product_name'] == u'Employee SKU':
                for act_key in [rhel_6_ak, rhel_6_partial_ak]:
                    act_key.add_subscriptions(data={
                        u'subscription_id': sub.id
                    })
                sub_found = True
        assert sub_found

        # Step 15: Enable product content in activation keys
        for act_key in [rhel_6_ak, rhel_6_partial_ak]:
            act_key.content_override(data={'content_override': {
                u'content_label': PRD_SETS['rhel6_sat6tools']['label'],
                u'value': u'1'
            }})

        # Step 16: Create three client machines and register them to satellite
        # Register the first vm with rhel_6_ak and the other two vms with
        # rhel_6_partial_ak
        cls.vm = [
            VirtualMachine(distro='rhel67', tag='incupdate')
            for _ in range(3)
        ]
        cls.setup_vm(cls.vm[0], rhel_6_ak.name, cls.org.label)
        for i in range(1, 3):
            cls.setup_vm(cls.vm[i], rhel_6_partial_ak.name, cls.org.label)

        # Find the content hosts (systems) and save them
        systems = System(organization=cls.org).search()
        cls.systems = []
        cls.partial_systems = []

        for system in systems:
            if system.content_view.read().name == cls.rhel_6_cv.name:
                cls.systems.append(system)
            else:
                cls.partial_systems.append(system)

    @classmethod
    def tearDownClass(cls):
        """Destroys all provisioned vms"""
        for virt_machine in cls.vm:
            virt_machine.destroy()
        entity_mixins.TASK_TIMEOUT = cls.old_task_timeout

    @staticmethod
    def setup_vm(client, act_key, org_name):
        """Creates the vm and registers it to the satellite"""
        client.create()
        client.install_katello_ca()

        # Register content host, install katello-agent
        result = client.register_contenthost(
            act_key,
            org_name,
            releasever='6.7'
        )
        assert result.return_code == 0
        result = client.install_katello_agent()
        client.run('katello-package-upload')

    @staticmethod
    def get_applicable_errata(repo):
        """Retrieves applicable errata for the given repo"""
        return Errata(repository=repo).search(
            query={'errata_restrict_applicable': True}
        )

    @run_only_on('sat')
    def test_api_inc_update_noapply(self):
        """@Test: Check if api incremental update can be done without
        actually applying it

        @Feature: Incremental Update

        @Setup:  The prerequisites are already covered in the setUpClass() but
        for easy debug, get the content view id, Repository id and Lifecycle
        environment id using hammer and plug these statements on the top of the
        test. For example::

            self.rhel_6_partial_cv = ContentView(id=38).read()
            self.rhel_66_repo = Repository(id=164).read()
            self.qe_lce = LifecycleEnvironment(id=46).read()

        @Assert: Incremental update completed with no errors and Content view
        has a newer version
        """
        # Get the content view versions and use the recent one.  API always
        # returns the versions in ascending order so it is safe to assume the
        # last one in the list is the recent
        cv_versions = self.rhel_6_partial_cv.version

        # Get the applicable errata
        errata_list = self.get_applicable_errata(self.rhel_66_repo)
        self.assertGreater(len(errata_list), 0)

        # Apply incremental update using the first applicable errata
        ContentViewVersion().incremental_update(data={
            'content_view_version_environments': [{
                'content_view_version_id': cv_versions[-1].id,
                'environment_ids': [self.qe_lce.id]
            }],
            'add_content': {
                'errata_ids': [errata_list[0].id]
            }
        })

        # Re-read the content view to get the latest versions
        self.rhel_6_partial_cv = self.rhel_6_partial_cv.read()
        self.assertGreater(
            len(self.rhel_6_partial_cv.version),
            len(cv_versions)
        )

    @skip_if_bug_open('bugzilla', 1259057)
    @run_only_on('sat')
    def test_cli_inc_update_noapply(self):
        """@Test: Check if cli incremental update can be done without
        actually applying it

        @Feature: Incremental Update

        @Assert: Incremental update completed with no errors and Content view
        has a newer version

        """
        # Get the content view versions and use the recent one.  API always
        # returns the versions in ascending order so it is safe to assume the
        # last one in the list is the recent

        cv_versions = self.rhel_6_partial_cv.version

        # Get the applicable errata
        errata_list = self.get_applicable_errata(self.rhel_66_repo)
        self.assertGreater(len(errata_list), 0)

        # Apply incremental update using the first applicable errata
        ContentViewCLI.version_incremental_update({
            u'content-view-version-id': cv_versions[-1].id,
            u'environment-ids': self.qe_lce.id,
            u'errata-ids': errata_list[0].id,
        })

        # Re-read the content view to get the latest versions
        self.rhel_6_partial_cv = self.rhel_6_partial_cv.read()
        self.assertGreater(
            len(self.rhel_6_partial_cv.version),
            len(cv_versions)
        )
