"""Test class for Subscriptions

:Requirement: Subscription

:CaseAutomation: Automated

:CaseComponent: SubscriptionManagement

:team: Phoenix-subscriptions

:CaseImportance: High

"""

from fauxfactory import gen_string
from manifester import Manifester
import pytest

from robottelo.config import settings
from robottelo.constants import EXPIRED_MANIFEST, PRDS, REPOS, REPOSET, DataFile
from robottelo.exceptions import CLIReturnCodeError

pytestmark = [pytest.mark.run_in_one_thread]


def test_positive_manifest_upload(function_sca_manifest_org, module_target_sat):
    """upload manifest

    :id: e5a0e4f8-fed9-4896-87a0-ac33f6baa227

    :expectedresults: Manifest are uploaded properly

    :CaseImportance: Critical
    """

    module_target_sat.cli.Subscription.list(
        {'organization-id': function_sca_manifest_org.id}, per_page=False
    )


@pytest.mark.upgrade
def test_positive_manifest_delete(function_sca_manifest_org, module_target_sat):
    """Delete uploaded manifest

    :id: 01539c07-00d5-47e2-95eb-c0fd4f39090f

    :expectedresults: Manifest are deleted properly

    :CaseImportance: Critical
    """
    module_target_sat.cli.Subscription.list(
        {'organization-id': function_sca_manifest_org.id}, per_page=False
    )
    module_target_sat.cli.Subscription.delete_manifest(
        {'organization-id': function_sca_manifest_org.id}
    )
    module_target_sat.cli.Subscription.list(
        {'organization-id': function_sca_manifest_org.id}, per_page=False
    )


@pytest.mark.upgrade
def test_positive_enable_manifest_reposet(function_sca_manifest_org, module_target_sat):
    """enable repository set

    :id: cc0f8f40-5ea6-4fa7-8154-acdc2cb56b45

    :expectedresults: you are able to enable and synchronize repository
        contained in a manifest

    :CaseImportance: Critical
    """
    module_target_sat.cli.Subscription.list(
        {'organization-id': function_sca_manifest_org.id}, per_page=False
    )
    module_target_sat.cli.RepositorySet.enable(
        {
            'basearch': 'x86_64',
            'name': REPOSET['rhva6'],
            'organization-id': function_sca_manifest_org.id,
            'product': PRDS['rhel'],
            'releasever': '6Server',
        }
    )
    module_target_sat.cli.Repository.synchronize(
        {
            'name': REPOS['rhva6']['name'],
            'organization-id': function_sca_manifest_org.id,
            'product': PRDS['rhel'],
        }
    )


def test_positive_manifest_history(function_sca_manifest_org, module_target_sat):
    """upload manifest and check history

    :id: 000ab0a0-ec1b-497a-84ff-3969a965b52c

    :expectedresults: Manifest history is shown properly

    :CaseImportance: Medium
    """
    org = function_sca_manifest_org
    module_target_sat.cli.Subscription.list({'organization-id': org.id}, per_page=None)
    history = module_target_sat.cli.Subscription.manifest_history({'organization-id': org.id})
    assert f'{org.name} file imported successfully.' in ''.join(history)


@pytest.mark.upgrade
def test_positive_manifest_refresh(function_sca_manifest_org, module_target_sat):
    """upload manifest and refresh

    :id: 579bbbf7-11cf-4d78-a3b1-16d73bd4ca57

    :expectedresults: Manifests can be refreshed

    :CaseImportance: Critical
    """
    module_target_sat.cli.Subscription.list(
        {'organization-id': function_sca_manifest_org.id}, per_page=False
    )
    module_target_sat.cli.Subscription.refresh_manifest(
        {'organization-id': function_sca_manifest_org.id}
    )
    module_target_sat.cli.Subscription.delete_manifest(
        {'organization-id': function_sca_manifest_org.id}
    )


def test_positive_subscription_list(function_sca_manifest_org, module_target_sat):
    """Verify that subscription list contains start and end date as well as product host count

    :id: 4861bcbc-785a-436d-98ce-14cfef7d6907

    :expectedresults: subscription list contains the start-date, end-date and product-host-count

    :customerscenario: true

    :BZ: 1686916

    :Verifies: SAT-31827

    :CaseImportance: Medium
    """
    subscription_list = module_target_sat.cli.Subscription.list(
        {'organization-id': function_sca_manifest_org.id}, per_page=False
    )
    for column in ['start-date', 'end-date', 'product-host-count']:
        assert column in subscription_list[0]


def test_positive_delete_manifest_as_another_user(target_sat, function_sca_manifest):
    """Verify that uploaded manifest if visible and deletable
        by a different user than the one who uploaded it

    :id: 4861bcbc-785a-436d-98cf-13cfef7d6907

    :expectedresults: manifest is refreshed

    :customerscenario: true

    :BZ: 1669241

    :CaseImportance: Medium
    """
    org = target_sat.api.Organization().create()
    user1_password = gen_string('alphanumeric')
    user1 = target_sat.api.User(
        admin=True, password=user1_password, organization=[org], default_organization=org
    ).create()
    user2_password = gen_string('alphanumeric')
    user2 = target_sat.api.User(
        admin=True, password=user2_password, organization=[org], default_organization=org
    ).create()
    # use the first admin to upload a manifest
    target_sat.put(f'{function_sca_manifest.path}', f'{function_sca_manifest.name}')
    target_sat.cli.Subscription.with_user(username=user1.login, password=user1_password).upload(
        {'file': f'{function_sca_manifest.name}', 'organization-id': f'{org.id}'}
    )
    # try to search and delete the manifest with another admin
    target_sat.cli.Subscription.with_user(
        username=user2.login, password=user2_password
    ).delete_manifest({'organization-id': org.id})
    assert len(target_sat.cli.Subscription.list({'organization-id': org.id})) == 0


@pytest.mark.stubbed
def test_positive_subscription_status_disabled_golden_ticket():
    """Verify that Content host Subscription status is set to 'Disabled'
     for a golden ticket manifest

    :id: 42e10499-3a0d-48cd-ab71-022421a74add

    :expectedresults: subscription status is 'Disabled'

    :customerscenario: true

    :BZ: 1789924

    :CaseImportance: Medium
    """


@pytest.mark.stubbed
def test_positive_candlepin_events_processed_by_STOMP():
    """Verify that Candlepin events are being read and processed by
       attaching subscriptions, validating host subscriptions status,
       and viewing processed and failed Candlepin events

    :id: d54a7652-f87d-4277-a0ec-a153e27b4487

    :steps:

        1. Register Content Host without subscriptions attached
        2. Verify subscriptions status is invalid
        3. Import a Manifest
        4. Attach subs to content host
        5. Verify subscription status is green, "valid", with
           "hammer subscription list --host-id x"
        6. Check for processed and failed Candlepin events

    :expectedresults: Candlepin events are being read and processed
                      correctly without any failures
    :BZ: 1826515

    :CaseImportance: High
    """


def test_negative_check_katello_reimport(request, target_sat, function_org):
    """Verify katello:reimport trace should not fail with an TypeError

    :id: b7508a1c-7798-4649-83a3-cf94c7409c96

    :steps:
        1. Import expired manifest & refresh
        2. Delete expired manifest
        3. Re-import new valid manifest & refresh

    :expectedresults: There should not be an error after reimport manifest

    :customerscenario: true

    :BZ: 2225534, 2253621
    """
    request.addfinalizer(lambda: function_org.delete())
    remote_path = f'/tmp/{EXPIRED_MANIFEST}'
    target_sat.put(DataFile.EXPIRED_MANIFEST_FILE, remote_path)
    # Import expired manifest & refresh
    target_sat.cli.Subscription.upload({'organization-id': function_org.id, 'file': remote_path})
    with pytest.raises(CLIReturnCodeError):
        target_sat.cli.Subscription.refresh_manifest({'organization-id': function_org.id})
    exec_val = target_sat.execute(
        'grep -i "Katello::HttpErrors::BadRequest: This Organization\'s subscription '
        'manifest has expired. Please import a new manifest" /var/log/foreman/production.log'
    )
    assert exec_val.status == 0
    # Delete expired manifest
    target_sat.cli.Subscription.delete_manifest({'organization-id': function_org.id})
    # Re-import new manifest & refresh
    manifester = Manifester(manifest_category=settings.manifest.golden_ticket)
    manifest = manifester.get_manifest()
    target_sat.upload_manifest(function_org.id, manifest.content)
    request.addfinalizer(
        lambda: target_sat.cli.Subscription.delete_manifest({'organization-id': function_org.id})
    )
    ret_val = target_sat.cli.Subscription.refresh_manifest({'organization-id': function_org.id})
    assert 'Candlepin job status: SUCCESS' in ret_val
    # Additional check, katello:reimport trace should not fail with TypeError
    trace_output = target_sat.execute("foreman-rake katello:reimport --trace")
    assert 'TypeError: no implicit conversion of String into Integer' not in trace_output.stdout
    assert trace_output.status == 0
