"""Tests for Red Hat Access Insights Client rpm

:Requirement: Rhai Client

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: RHCloud-Insights

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_alpha
from nailgun import entities

from robottelo import manifests
from robottelo.api.utils import upload_manifest
from robottelo.constants import DEFAULT_SUBSCRIPTION_NAME
from robottelo.constants import DISTRO_DEFAULT
from robottelo.decorators import skip_if_not_set
from robottelo.vm import VirtualMachine


@pytest.fixture(scope='module')
def org():
    """Create a new organization with name prefix 'insights_'"""
    return entities.Organization(name=gen_alpha(15, start='insights_')).create()


@pytest.fixture(scope='module')
def manifest_org(org):
    """Upload manifest to organization."""
    with manifests.clone() as manifest:
        upload_manifest(org.id, manifest.content)
    return org


@pytest.fixture(scope='module')
def activation_key(manifest_org):
    """Create activation key using default CV and library environment."""
    activation_key = entities.ActivationKey(
        auto_attach=True,
        content_view=manifest_org.default_content_view.id,
        environment=manifest_org.library.id,
        name=gen_alpha(),
        organization=manifest_org,
    ).create()

    # Find the 'Red Hat Employee Subscription' and attach it to the activation key.
    for subs in entities.Subscription(organization=manifest_org).search():
        if subs.name == DEFAULT_SUBSCRIPTION_NAME:
            # 'quantity' must be 1, not subscription['quantity']. Greater
            # values produce this error: 'RuntimeError: Error: Only pools
            # with multi-entitlement product subscriptions can be added to
            # the activation key with a quantity greater than one.'
            activation_key.add_subscriptions(data={'quantity': 1, 'subscription_id': subs.id})
            break
    return activation_key


@pytest.mark.skip_if_open('BZ:1892405')
@skip_if_not_set('clients')
@pytest.mark.run_in_one_thread
def test_positive_connection_option(org, activation_key):
    """Verify that 'insights-client --test-connection' successfully tests the proxy connection via
    the Satellite.

    :id: 167758c9-cbfa-4a81-9a11-27f88aaf9118

    :expectedresults: 'insights-client --test-connection' should return 0 on a client that is
        successfully registered to RHAI through Satellite.
    """
    with VirtualMachine(distro=DISTRO_DEFAULT) as vm:
        vm.configure_rhai_client(activation_key.name, org.label, DISTRO_DEFAULT)
        result = vm.run('insights-client --test-connection')
        assert result.return_code == 0, (
            'insights-client --test-connection failed.\n'
            f'return_code: {result.return_code}\n'
            f'stdout: {result.stdout}\n'
            f'stderr: {result.stderr}'
        )
