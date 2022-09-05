"""Test class for the capsule CLI.

:Requirement: Capsule

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: Capsule

:Assignee: vsedmik

:TestType: Functional

:CaseImportance: Critical

:Upstream: No
"""
import pytest
from fauxfactory import gen_alphanumeric
from fauxfactory import gen_string

from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import CLIFactoryError
from robottelo.cli.proxy import Proxy
from robottelo.datafactory import parametrized
from robottelo.datafactory import valid_data_list


pytestmark = [pytest.mark.run_in_one_thread]


def _make_proxy(request, target_sat, options=None):
    """Create a Proxy and add the finalizer"""
    proxy = target_sat.cli_factory.make_proxy(options)

    @request.addfinalizer
    def _cleanup():
        target_sat.cli.Proxy.delete({'id': proxy['id']})

    return proxy


@pytest.mark.skip_if_not_set('fake_capsules')
@pytest.mark.tier1
def test_negative_create_with_url(target_sat):
    """Proxy creation with random URL

    :id: 9050b362-c710-43ba-9d77-7680b8f9ed8c

    :expectedresults: Proxy is not created

    :CaseLevel: Component

    """
    # Create a random proxy
    with pytest.raises(CLIFactoryError, match='Could not create the proxy:'):
        target_sat.cli_factory.make_proxy(
            {
                'url': f"http://{gen_string('alpha', 6)}:{gen_string('numeric', 4)}",
            }
        )


@pytest.mark.skip_if_not_set('fake_capsules')
@pytest.mark.tier1
@pytest.mark.parametrize('name', **parametrized(valid_data_list()))
def test_positive_create_with_name(request, target_sat, name):
    """Proxy creation with the home proxy

    :id: 7decd7a3-2d35-43ff-9a20-de44e83c7389

    :expectedresults: Proxy is created

    :CaseLevel: Component

    :Parametrized: Yes

    :BZ: 1398695
    """
    proxy = _make_proxy(request, target_sat, options={'name': name})
    assert proxy['name'] == name


@pytest.mark.skip_if_not_set('fake_capsules')
@pytest.mark.tier1
@pytest.mark.parametrize('name', **parametrized(valid_data_list()))
def test_positive_delete_by_id(name, target_sat):
    """Proxy deletion with the home proxy

    :id: 1b6973b1-259d-4866-b36f-c2d5fb154035

    :expectedresults: Proxy is deleted

    :CaseLevel: Component

    :Parametrized: Yes

    :BZ: 1398695
    """
    proxy = target_sat.cli_factory.make_proxy({'name': name})
    Proxy.delete({'id': proxy['id']})
    with pytest.raises(CLIReturnCodeError):
        Proxy.info({'id': proxy['id']})


@pytest.mark.skip_if_not_set('fake_capsules')
@pytest.mark.tier1
def test_positive_update_name(request, target_sat):
    """Proxy name update with the home proxy

    :id: 1a02a06b-e9ab-4b9b-bcb0-ac7060188316

    :expectedresults: Proxy has the name updated

    :CaseLevel: Component

    :BZ: 1398695
    """
    proxy = _make_proxy(request, target_sat, options={'name': gen_alphanumeric()})
    for new_name in valid_data_list().values():
        newport = target_sat.available_capsule_port
        with target_sat.default_url_on_new_port(9090, newport) as url:
            Proxy.update({'id': proxy['id'], 'name': new_name, 'url': url})
            proxy = Proxy.info({'id': proxy['id']})
            assert proxy['name'] == new_name


@pytest.mark.skip_if_not_set('fake_capsules')
@pytest.mark.tier2
def test_positive_refresh_features_by_id(request, target_sat):
    """Refresh smart proxy features, search for proxy by id

    :id: d3db63ce-b877-40eb-a863-294c12489ddd

    :expectedresults: Proxy features are refreshed

    :CaseLevel: Integration

    :CaseImportance: High

    """
    # Since we want to run multiple commands against our fake capsule, we
    # need the tunnel kept open in order not to allow different concurrent
    # test to claim it. Thus we want to manage the tunnel manually.

    # get an available port for our fake capsule
    port = target_sat.available_capsule_port
    with target_sat.default_url_on_new_port(9090, port) as url:
        proxy = _make_proxy(request, target_sat, options={'url': url})
        Proxy.refresh_features({'id': proxy['id']})


@pytest.mark.skip_if_not_set('fake_capsules')
@pytest.mark.tier2
def test_positive_refresh_features_by_name(request, target_sat):
    """Refresh smart proxy features, search for proxy by name

    :id: 2ddd0097-8f65-430e-963d-a3b5dcffe86b

    :expectedresults: Proxy features are refreshed

    :CaseLevel: Integration

    :CaseImportance: High

    """
    # Since we want to run multiple commands against our fake capsule, we
    # need the tunnel kept open in order not to allow different concurrent
    # test to claim it. Thus we want to manage the tunnel manually.

    # get an available port for our fake capsule
    port = target_sat.available_capsule_port
    with target_sat.default_url_on_new_port(9090, port) as url:
        proxy = _make_proxy(request, target_sat, options={'url': url})
        Proxy.refresh_features({'id': proxy['name']})


@pytest.mark.skip_if_not_set('fake_capsules')
@pytest.mark.tier1
def test_positive_import_puppet_classes(session_puppet_enabled_sat, puppet_proxy_port_range):
    """Import puppet classes from proxy

    :id: 42e3a9c0-62e1-4049-9667-f3c0cdfe0b04

    :expectedresults: Puppet classes are imported from proxy

    :CaseLevel: Component

    """
    with session_puppet_enabled_sat as puppet_sat:
        port = puppet_sat.available_capsule_port
        with puppet_sat.default_url_on_new_port(9090, port) as url:
            proxy = puppet_sat.cli_factory.make_proxy({'url': url})
            Proxy.import_classes({'id': proxy['id']})
        Proxy.delete({'id': proxy['id']})


@pytest.mark.stubbed
def test_positive_provision():
    """User can provision through a capsule

    :id: 1b91e6ed-56bb-4a21-9b69-8b41242458c5

    :Setup: Some valid, functional compute resource (perhaps one variation
        of this case for each supported compute resource type). Also,
        functioning capsule with proxy is required.

    :Steps:

        1. Attempt to route provisioning content through capsule that is
           using a proxy
        2. Attempt to provision instance

    :expectedresults: Instance can be provisioned, with content coming
        through proxy-enabled capsule.

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
def test_positive_register():
    """User can register system through proxy-enabled capsule

    :id: dc544ec8-0320-4897-a6ca-ce9ebad27975

    :Steps: attempt to register a system trhough a proxy-enabled capsule

    :expectedresults: system is successfully registered

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
def test_positive_unregister():
    """User can unregister system through proxy-enabled capsule

    :id: 9b7714da-74be-4c0a-9209-9d15c2c98eaa

    :Steps: attempt to unregister a system through a proxy-enabled capsule

    :expectedresults: system is successfully unregistered

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
def test_positive_subscribe():
    """User can subscribe system to content through proxy-enabled
    capsule

    :id: 091bba73-bc78-4b8c-ac27-5c10e9838cfb

    :Setup: Content source types configured/synced for [RH, Custom, Puppet,
        Docker] etc.

    :Steps: attempt to subscribe a system to a content type variation, via
        a proxy-enabled capsule

    :expectedresults: system is successfully subscribed to each content
        type

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
def test_positive_consume_content():
    """User can consume content on system, from a content source,
    through proxy-enabled capsule

    :id: a3fb9879-7799-4743-99a8-963701e687c1

    :Setup: Content source types configured/synced for [RH, Custom, Puppet,
        Docker] etc.

    :Steps:

        1. attempt to subscribe a system to a content type variation, via a
           proxy-enabled capsule
        2. Attempt to install content RPMs via
           proxy-enabled capsule

    :expectedresults: system successfully consume content

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
def test_positive_unsubscribe():
    """User can unsubscribe system from content through
    proxy-enabled capsule

    :id: 0d34713d-3d60-4e5a-ada6-9a24aa865cb4

    :Setup: Content source types configured/synced for [RH, Custom, Puppet]
        etc.

    :Steps:

        1. attempt to subscribe a system to a content type variation, via a
           proxy-enabled capsule
        2. attempt to unsubscribe a system from said content type(s) via a
           proxy-enabled capsule

    :expectedresults: system is successfully unsubscribed from each content
        type

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
def test_positive_reregister_with_capsule_cert():
    """system can register via capsule using cert provided by
    the capsule itself.

    :id: 785b94ea-ffbf-4c18-8160-f705e3d7cbe6

    :Setup: functional capsule and certs rpm installed on target client.

    :Steps:

        1. Attempt to register from parent satellite; unregister and remove
           cert rpm
        2. Attempt to reregister using same credentials and certs from a
           functional capsule.

    :expectedresults: Registration works , and certs RPM installed from
        capsule.

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
def test_positive_ssl_capsule():
    """Assure SSL functionality for capsules

    :id: 4d19bee6-15d4-4fd5-b3de-9144608cdba7

    :Setup: A capsule installed with SSL enabled.

    :Steps: Execute basic steps from above (register, subscribe, consume,
        unsubscribe, unregister) while connected to a capsule that is
        SSL-enabled

    :expectedresults: No failures executing said test scenarios against
        SSL, baseline functionality identical to non-SSL

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
def test_positive_enable_bmc():
    """Enable BMC feature on smart-proxy

    :id: 9cc4db2f-3bec-4e51-89a2-18a0a6167012

    :Setup: A capsule installed with SSL enabled.

    :Steps:

        1. Enable BMC feature on proxy by running installer with:
           ``katello-installer --foreman-proxy-bmc 'true'``
        2. Please make sure to check default values to other BMC options.
           Should be like below: ``--foreman-proxy-bmc-default-provider
           BMC default provider.  (default: "ipmitool")``
           ``--foreman-proxy-bmc-listen-on  BMC proxy to listen on https,
           http, or both (default: "https")``
        3. Check if BMC plugin is enabled with: ``#cat
           /etc/foreman-proxy/settings.d/bmc.yml | grep enabled``
        4. Restart foreman-proxy service

    :expectedresults: Katello installer should show the options to enable
        BMC

    :CaseAutomation: NotAutomated
    """
