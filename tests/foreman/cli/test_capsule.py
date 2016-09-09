# -*- encoding: utf-8 -*-
"""Test class for the capsule CLI.

@Requirement: Capsule

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: CLI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""

from fauxfactory import gen_alphanumeric, gen_string
from robottelo.cleanup import capsule_cleanup
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import CLIFactoryError, make_proxy
from robottelo.cli.proxy import Proxy
from robottelo.datafactory import valid_data_list
from robottelo.decorators import (
    run_only_on, stubbed, tier1, tier2, skip_if_not_set
    )
from robottelo.helpers import (
    default_url_on_new_port,
    get_available_capsule_port
)
from robottelo.config import settings
from robottelo.test import CLITestCase


class CapsuleTestCase(CLITestCase):
    """Proxy cli tests"""

    @skip_if_not_set('fake_capsules')
    @run_only_on('sat')
    @tier1
    def test_negative_create_with_url(self):
        """Proxy creation with random URL

        @id: 9050b362-c710-43ba-9d77-7680b8f9ed8c

        @Assert: Proxy is not created
        """
        # Create a random proxy
        with self.assertRaisesRegex(
            CLIFactoryError,
            u'Could not create the proxy:'
        ):
            make_proxy({
                u'url': u'http://{0}:{1}'.format(
                    gen_string('alpha', 6),
                    gen_string('numeric', 4)),
            })

    @skip_if_not_set('fake_capsules')
    @run_only_on('sat')
    @tier1
    def test_positive_create_with_name(self):
        """Proxy creation with the home proxy

        @id: 7decd7a3-2d35-43ff-9a20-de44e83c7389

        @Assert: Proxy is created
        """
        for name in valid_data_list():
            with self.subTest(name):
                proxy = make_proxy({u'name': name})
                self.assertEquals(proxy['name'], name)
                # Add capsule id to cleanup list
                self.addCleanup(capsule_cleanup, proxy['id'])

    @skip_if_not_set('fake_capsules')
    @run_only_on('sat')
    @tier1
    def test_positive_delete_by_id(self):
        """Proxy deletion with the home proxy

        @id: 1b6973b1-259d-4866-b36f-c2d5fb154035

        @Assert: Proxy is deleted
        """
        for name in valid_data_list():
            with self.subTest(name):
                proxy = make_proxy({u'name': name})
                Proxy.delete({u'id': proxy['id']})
                with self.assertRaises(CLIReturnCodeError):
                    Proxy.info({u'id': proxy['id']})

    @skip_if_not_set('fake_capsules')
    @run_only_on('sat')
    @tier1
    def test_positive_update_name(self):
        """Proxy name update with the home proxy

        @id: 1a02a06b-e9ab-4b9b-bcb0-ac7060188316

        @Assert: Proxy has the name updated
        """
        proxy = make_proxy({u'name': gen_alphanumeric()})
        for new_name in valid_data_list():
            with self.subTest(new_name):
                newport = get_available_capsule_port()
                with default_url_on_new_port(9090, newport) as url:
                    Proxy.update({
                        u'id': proxy['id'],
                        u'name': new_name,
                        u'url': url,
                    })
                    proxy = Proxy.info({u'id': proxy['id']})
                    self.assertEqual(proxy['name'], new_name)
        # Add capsule id to cleanup list
        self.addCleanup(capsule_cleanup, proxy['id'])

    @skip_if_not_set('fake_capsules')
    @run_only_on('sat')
    @tier2
    def test_positive_refresh_features_by_id(self):
        """Refresh smart proxy features, search for proxy by id

        @id: d3db63ce-b877-40eb-a863-294c12489ddd

        @Assert: Proxy features are refreshed

        @CaseLevel: Integration
        """
        # Since we want to run multiple commands against our fake capsule, we
        # need the tunnel kept open in order not to allow different concurrent
        # test to claim it. Thus we want to manage the tunnel manually.

        # get an available port for our fake capsule
        port = get_available_capsule_port()
        with default_url_on_new_port(9090, port):
            url = u'https://{0}:{1}'.format(settings.server.hostname, port)
            proxy = make_proxy({u'url': url})
            Proxy.refresh_features({u'id': proxy['id']})
        # Add capsule id to cleanup list
        self.addCleanup(capsule_cleanup, proxy['id'])

    @skip_if_not_set('fake_capsules')
    @run_only_on('sat')
    @tier2
    def test_positive_refresh_features_by_name(self):
        """Refresh smart proxy features, search for proxy by name

        @id: 2ddd0097-8f65-430e-963d-a3b5dcffe86b

        @Assert: Proxy features are refreshed

        @CaseLevel: Integration
        """
        # Since we want to run multiple commands against our fake capsule, we
        # need the tunnel kept open in order not to allow different concurrent
        # test to claim it. Thus we want to manage the tunnel manually.

        # get an available port for our fake capsule
        port = get_available_capsule_port()
        with default_url_on_new_port(9090, port):
            url = u'https://{0}:{1}'.format(settings.server.hostname, port)
            proxy = make_proxy({u'url': url})
            Proxy.refresh_features({u'id': proxy['name']})
        # Add capsule id to cleanup list
        self.addCleanup(capsule_cleanup, proxy['id'])


class CapsuleIntegrationTestCase(CLITestCase):
    """Tests for capsule functionality."""

    @stubbed()
    def test_positive_provision(self):
        """User can provision through a capsule

        @id: 1b91e6ed-56bb-4a21-9b69-8b41242458c5

        @Setup: Some valid, functional compute resource (perhaps one variation
        of this case for each supported compute resource type). Also,
        functioning capsule with proxy is required.

        @Steps:

        1. Attempt to route provisioning content through capsule that is using
           a proxy
        2. Attempt to provision instance

        @Assert: Instance can be provisioned, with content coming through
        proxy-enabled capsule.

        @caseautomation: notautomated
        """

    @stubbed()
    def test_positive_register(self):
        """User can register system through proxy-enabled capsule

        @id: dc544ec8-0320-4897-a6ca-ce9ebad27975

        @Steps:

        1. attempt to register a system trhough a proxy-enabled capsule

        @Assert: system is successfully registered

        @caseautomation: notautomated
        """

    @stubbed()
    def test_positive_unregister(self):
        """User can unregister system through proxy-enabled capsule

        @id: 9b7714da-74be-4c0a-9209-9d15c2c98eaa

        @Steps:

        1. attempt to unregister a system through a proxy-enabled capsule

        @Assert: system is successfully unregistered

        @caseautomation: notautomated
        """

    @stubbed()
    def test_positive_subscribe(self):
        """User can subscribe system to content through proxy-enabled
        capsule

        @id: 091bba73-bc78-4b8c-ac27-5c10e9838cfb

        @Setup: Content source types configured/synced for [RH, Custom, Puppet,
        Docker] etc.

        @Steps:

        1. attempt to subscribe a system to a content type variation, via a
           proxy-enabled capsule

        @Assert: system is successfully subscribed to each content type

        @caseautomation: notautomated
        """

    @stubbed()
    def test_positive_consume_content(self):
        """User can consume content on system, from a content source,
        through proxy-enabled capsule

        @id: a3fb9879-7799-4743-99a8-963701e687c1

        @Setup: Content source types configured/synced for [RH, Custom, Puppet,
        Docker] etc.

        @Steps:

        1. attempt to subscribe a system to a content type variation, via a
           proxy-enabled capsule
        2. Attempt to install content (RPMs, puppet modules) via proxy-enabled
           capsule

        @Assert: system successfully consume content

        @caseautomation: notautomated
        """

    @stubbed()
    def test_positive_unsubscribe(self):
        """User can unsubscribe system from content through
        proxy-enabled capsule

        @id: 0d34713d-3d60-4e5a-ada6-9a24aa865cb4

        @Setup: Content source types configured/synced for [RH, Custom, Puppet]
        etc.

        @Steps:

        1. attempt to subscribe a system to a content type variation, via a
           proxy-enabled capsule
        2. attempt to unsubscribe a system from said content type(s) via a
           proxy-enabled capsule

        @Assert: system is successfully unsubscribed from each content type

        @caseautomation: notautomated
        """

    @stubbed()
    def test_positive_reregister_with_capsule_cert(self):
        """system can register via capsule using cert provided by
        the capsule itself.

        @id: 785b94ea-ffbf-4c18-8160-f705e3d7cbe6

        @Setup: functional capsule and certs rpm installed on target client.

        @Steps:

        1. Attempt to register from parent satellite; unregister and remove
           cert rpm
        2. Attempt to reregister using same credentials and certs from a
           functional capsule.

        @Assert: Registration works , and certs RPM installed
        from capsule.

        @caseautomation: notautomated
        """

    @stubbed()
    def test_positive_ssl_capsule(self):
        """Assure SSL functionality for capsules

        @id: 4d19bee6-15d4-4fd5-b3de-9144608cdba7

        @Setup: A capsule installed with SSL enabled.

        @Steps:

        1. Execute basic steps from above (register, subscribe, consume,
           unsubscribe, unregister) while connected to a capsule that is
           SSL-enabled

        @Assert: No failures executing said test scenarios against SSL,
        baseline functionality identical to non-SSL

        @caseautomation: notautomated
        """

    @stubbed()
    def test_positive_enable_bmc(self):
        """Enable BMC feature on smart-proxy

        @id: 9cc4db2f-3bec-4e51-89a2-18a0a6167012

        @Setup: A capsule installed with SSL enabled.

        @Steps:

        1. Enable BMC feature on proxy by running installer with:
           ``katello-installer --foreman-proxy-bmc 'true'``
        2. Please make sure to check default values to other BMC options.
           Should be like below:
           ``--foreman-proxy-bmc-default-provider  BMC default provider.
           (default: "ipmitool")``
           ``--foreman-proxy-bmc-listen-on  BMC proxy to listen on https, http,
           or both (default: "https")``
        3. Check if BMC plugin is enabled with:
           ``#cat /etc/foreman-proxy/settings.d/bmc.yml | grep enabled``
        4. Restart foreman-proxy service

        @Assert: Katello installer should show the options to enable BMC

        @caseautomation: notautomated
        """
