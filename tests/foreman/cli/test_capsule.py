"""Test class for the capsule CLI.

:Requirement: ForemanProxy

:CaseAutomation: Automated

:CaseComponent: ForemanProxy

:Team: Platform

:CaseImportance: Critical

"""

import pytest

pytestmark = [pytest.mark.run_in_one_thread]


@pytest.mark.skip_if_not_set('fake_capsules')
@pytest.mark.tier1
def test_positive_import_puppet_classes(session_puppet_enabled_sat):
    """Import puppet classes from proxy

    :id: 42e3a9c0-62e1-4049-9667-f3c0cdfe0b04

    :expectedresults: Puppet classes are imported from proxy
    """
    with session_puppet_enabled_sat as puppet_sat:
        port = puppet_sat.available_capsule_port
        with puppet_sat.default_url_on_new_port(9090, port) as url:
            proxy = puppet_sat.cli_factory.make_proxy({'url': url})
            puppet_sat.cli.Proxy.import_classes({'id': proxy['id']})
        puppet_sat.cli.Proxy.delete({'id': proxy['id']})


@pytest.mark.stubbed
@pytest.mark.e2e
@pytest.mark.upgrade
def test_positive_capsule_content():
    """Registered and provisioned hosts can consume content from capsule

    :id: 7e5493de-b27b-4adc-ba18-4dc2e94e7305

    :Setup: Capsule with some content synced

    :steps:

        1. Register a host to the capsule
        2. Sync content from capsule to the host
        3. Unregister host from the capsule
        4. Provision host via capsule
        5. Provisioned host syncs content from capsule

    :expectedresults: Hosts can be successfully registered to the capsule,
        consume content and unregister afterwards. Hosts can be successfully
        provisioned via capsule and consume content as well.

    :CaseAutomation: NotAutomated
    """
