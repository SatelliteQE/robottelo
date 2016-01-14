"""Tests for the Oscap report upload feature"""
from fauxfactory import gen_string
from nailgun import entities
from robottelo import manifests, ssh
from robottelo.api.utils import (
    enable_rhrepo_and_fetchid,
    promote,
    upload_manifest,
)
from robottelo.config import settings
from robottelo.constants import (
    ANY_CONTEXT,
    DEFAULT_SUBSCRIPTION_NAME,
    OSCAP_DEFAULT_CONTENT,
    OSCAP_PERIOD,
    OSCAP_PROFILE,
    OSCAP_WEEKDAY,
    PRDS,
    REPOS,
    REPOSET,
)
from robottelo.decorators import run_only_on, skip_if_not_set, stubbed, tier4
from robottelo.test import UITestCase
from robottelo.ui.factory import set_context, make_hostgroup, make_oscappolicy
from robottelo.ui.session import Session
from robottelo.vm import VirtualMachine


class OpenScapTestCase(UITestCase):
    """Implements Product tests in UI"""

    @classmethod
    @skip_if_not_set('clients')
    def setUpClass(cls):
        """ Create an organization, environment, content view and activation key.

        1. Create new organization and environment
        2. Clone and upload manifest
        3. Sync a RedHat repository
        4. Create content-view
        5. Add repository to content-view
        6. Promote/publish content-view
        7. Create an activation-key
        8. Add product to activation-key

        """
        super(OpenScapTestCase, cls).setUpClass()
        repo_values = [
            {'repo': REPOS['rhst6']['name'], 'reposet': REPOSET['rhst6']},
            {'repo': REPOS['rhst7']['name'], 'reposet': REPOSET['rhst7']},
        ]

        # step 1: Create new organization and environment.
        org = entities.Organization(name=gen_string('alpha')).create()
        cls.org_name = org.name
        env = entities.LifecycleEnvironment(
            organization=org,
            name=gen_string('alpha')
        ).create()
        cls.env_name = env.name

        # step 2: Clone and Upload manifest
        with manifests.clone() as manifest:
            upload_manifest(org.id, manifest.content)

        # step 3: Sync RedHat Sattools RHEL6 ad RHEL7 repository
        repos = [
            entities.Repository(id=enable_rhrepo_and_fetchid(
                basearch='x86_64',
                org_id=org.id,
                product=PRDS['rhel'],
                repo=value['repo'],
                reposet=value['reposet'],
                releasever=None,
            ))
            for value in repo_values
        ]
        for repo in repos:
            repo.sync()

        # step 4: Create content view
        content_view = entities.ContentView(
            organization=org,
            name=gen_string('alpha')
        ).create()
        cls.cv_name = content_view.name

        # step 5: Associate repository to new content view
        content_view.repository = repos
        content_view = content_view.update(['repository'])

        # step 6: Publish content view and promote to lifecycle env.
        content_view.publish()
        content_view = content_view.read()
        promote(content_view.version[0], env.id)

        # step 7: Create activation key
        cls.ak_name = gen_string('alpha')
        activation_key = entities.ActivationKey(
            name=cls.ak_name,
            environment=env,
            organization=org,
            content_view=content_view,
        ).create()

        # step 7.1: Walk through the list of subscriptions.
        # Find the "Employee SKU" and attach it to the
        # recently-created activation key.
        for sub in entities.Subscription(organization=org).search():
            if sub.read_json()['product_name'] == DEFAULT_SUBSCRIPTION_NAME:
                # 'quantity' must be 1, not subscription['quantity']. Greater
                # values produce this error: "RuntimeError: Error: Only pools
                # with multi-entitlement product subscriptions can be added to
                # the activation key with a quantity greater than one."
                activation_key.add_subscriptions(data={
                    'quantity': 1,
                    'subscription_id': sub.id,
                })
                break
        for content_label in [REPOS['rhst6']['id'], REPOS['rhst7']['id']]:
            # step 7.2: Enable product content
            activation_key.content_override(data={'content_override': {
                u'content_label': content_label,
                u'value': u'1',
            }})

    @run_only_on('sat')
    @tier4
    def test_positive_upload_to_satellite(self):
        """Perform end to end oscap test and upload reports.

        @Feature: Oscap End to End.

        @Assert: Oscap reports from rhel6 and rhel7 clients should be
        uploaded to satellite6 and be searchable.

        """
        rhel6_repo = settings.rhel6_repo
        rhel7_repo = settings.rhel7_repo
        rhel6_content = OSCAP_DEFAULT_CONTENT['rhel6_content']
        rhel7_content = OSCAP_DEFAULT_CONTENT['rhel7_content']
        sat6_hostname = settings.server.hostname
        hgrp6_name = gen_string('alpha')
        hgrp7_name = gen_string('alpha')
        policy_values = [
            {
                'content': rhel6_content,
                'hgrp': hgrp6_name,
                'policy': gen_string('alpha'),
            },
            {
                'content': rhel7_content,
                'hgrp': hgrp7_name,
                'policy': gen_string('alpha'),
            },
        ]
        vm_values = [
            {
                'distro': 'rhel67',
                'hgrp': hgrp6_name,
                'rhel_repo': rhel6_repo,
            },
            {
                'distro': 'rhel71',
                'hgrp': hgrp7_name,
                'rhel_repo': rhel7_repo,
            },
        ]
        with Session(self.browser) as session:
            self.puppetclasses.import_scap_client_puppet_classes()
            set_context(session, org=ANY_CONTEXT['org'])
            # Creates oscap content for both rhel6 and rhel7
            for content in [rhel6_content, rhel7_content]:
                session.nav.go_to_oscap_content()
                self.oscapcontent.update(content, content_org=self.org_name)
            set_context(session, org=self.org_name)
            # Creates host_group for both rhel6 and rhel7
            for host_group in [hgrp6_name, hgrp7_name]:
                make_hostgroup(
                    session,
                    content_source=sat6_hostname,
                    name=host_group,
                    puppet_ca=sat6_hostname,
                    puppet_master=sat6_hostname,
                )
            # Creates oscap_policy for both rhel6 and rhel7.
            for value in policy_values:
                make_oscappolicy(
                    session,
                    content=value['content'],
                    host_group=value['hgrp'],
                    name=value['policy'],
                    period=OSCAP_PERIOD['weekly'],
                    profile=OSCAP_PROFILE['rhccp'],
                    period_value=OSCAP_WEEKDAY['friday'],
                )
            # Creates two vm's each for rhel6 and rhel7, runs
            # openscap scan and uploads report to satellite6.
            for value in vm_values:
                with VirtualMachine(distro=value['distro']) as vm:
                    host = vm.hostname
                    vm.install_katello_ca()
                    vm.register_contenthost(self.ak_name, self.org_name)
                    vm.configure_puppet(value['rhel_repo'])
                    session.nav.go_to_hosts()
                    set_context(session, org=ANY_CONTEXT['org'])
                    self.hosts.update_host_bulkactions(
                        host=host,
                        org=self.org_name
                    )
                    self.hosts.update(
                        cv=self.cv_name,
                        host_group=value['hgrp'],
                        lifecycle_env=self.env_name,
                        name=host,
                        reset_puppetenv=True,
                    )
                    session.nav.go_to_hosts()
                    # Run "puppet agent -t" twice so that it detects it's,
                    # satellite6 and fetch katello SSL certs.
                    for _ in range(2):
                        vm.run(u'puppet agent -t 2> /dev/null')
                    result = vm.run(
                        u'cat /etc/foreman_scap_client/config.yaml'
                        '| grep profile'
                    )
                    self.assertEqual(result.return_code, 0)
                    # BZ 1259188 , required till CH and Hosts unification.
                    # We need to re-register because of above bug and FE
                    vm.register_contenthost(self.ak_name, self.org_name)
                    # Runs the actual oscap scan on the vm/clients and
                    # uploads report to Internal Capsule.
                    vm.execute_foreman_scap_client()
                    # Runs the below command on Internal capsule to upload
                    # content to Satellite6 and thus make reports visible
                    # on UI.
                    ssh.command(u'smart-proxy-openscap-send')
                    # Assert whether oscap reports are uploaded to
                    # Satellite6.
                    session.nav.go_to_reports()
                    self.assertTrue(self.oscapreports.search(host))

    @run_only_on('sat')
    @stubbed
    @tier4
    def test_positive_has_arf_report_summary_page(self):
        """OSCAP ARF Report now has summary page

        @Feature: Oscap Reports

        @Steps:
        1. Make sure the oscap report with it's corresponding hostname
           is visible in the UI.
        2. Click on the host name to access the oscap report.

        @Assert: Oscap ARF reports should have summary page.

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed
    @tier4
    def test_positive_view_full_report_button(self):
        """'View full Report' button should exist for OSCAP Reports.

        @Feature: Oscap Reports

        @Steps:
        1. Make sure the oscap report with it's corresponding hostname
           is visible in the UI.
        2. Click on the host name to access the oscap report.

        @Assert: Should have 'view full report' button to view the
        actual HTML report.

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed
    @tier4
    def test_positive_download_xml_button(self):
        """'Download xml' button should exist for OSCAP Reports
        to be downloaded in xml format.

        @Feature: Oscap Reports

        @Steps:
        1. Make sure the oscap report with it's corresponding hostname
           is visible in the UI.
        2. Click on the host name to access the oscap report.

        @Assert: Should have 'Download xml in bzip' button to download
        the xml report.

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed
    @tier4
    def test_positive_select_oscap_proxy(self):
        """Oscap-Proxy select box should exist while filling hosts
        and host-groups form.

        @Feature: Oscap Proxy

        @Steps:
        1.Choose the Oscap Proxy/capsule appropriately for the host
          or host-groups.

        @Assert: Should have an Oscap-Proxy select box while filling
        hosts and host-groups form.

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed
    @tier4
    def test_positive_delete_multiple_arf_reports(self):
        """Multiple arf reports deletion should be possible.

        @Feature: Oscap Reports

        @Steps:
        1. Run Oscap scans are run for multiple Hosts.
        2. Make sure the oscap reports with it's corresponding hostnames
           are visible in the UI.
        3. Now select multiple reports from the checkbox and delete the
           reports.

        @Assert: Multiple Oscap ARF reports can be deleted.

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed
    @tier4
    def test_positive_reporting_emails_of_oscap_reports(self):
        """Email Reporting of oscap reports should be possible.

        @Feature: Oscap Reports

        @Assert: Whether email reporting of oscap reports is possible.

        @Status: Manual
        """
