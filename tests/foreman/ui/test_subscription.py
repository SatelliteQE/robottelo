"""Test module for Subscriptions/Manifests UI

:Requirement: Subscription

:CaseAutomation: Automated

:CaseComponent: SubscriptionManagement

:team: Phoenix-subscriptions

:CaseImportance: High

"""

from datetime import datetime, timedelta
from tempfile import mkstemp
import time
from zoneinfo import ZoneInfo

from fauxfactory import gen_string
import pytest
from tzlocal import get_localzone_name

from robottelo.constants import (
    DEFAULT_SUBSCRIPTION_NAME,
    EXPIRED_MANIFEST,
    EXPIRED_MANIFEST_DATE,
    DataFile,
)
from robottelo.utils.issue_handlers import is_open

pytestmark = [pytest.mark.run_in_one_thread]


@pytest.mark.e2e
@pytest.mark.upgrade
def test_positive_end_to_end(session, function_sca_manifest, target_sat):
    """Upload a manifest with minimal input parameters, attempt to
    delete it with checking the warning message and hit 'Cancel' button after than delete it.

    :id: 580fc072-01e0-4f83-8cbb-2a8522d76243

    :expectedresults:
        1. The manifest was uploaded successfully.
        2. Manifest import is reflected at the dashboard
        3. When attempting to delete the manifest the confirmation dialog contains informative
            message which warns user about downsides and consequences of manifest deletion.
        4. When hitting cancel the manifest was not deleted.
        5. When deleting and confirming deletion, the manifest was deleted successfully.
        6. When reimporting manifest, the manifest is reimported successfully and the candlepin log
            shows no error.

    :BZ: 1266827, 2066899, 2076684

    :SubComponent: Candlepin

    :customerscenario: true

    :CaseImportance: Critical
    """
    expected_message_lines = [
        'Are you sure you want to delete the manifest?',
        'Note: Deleting a subscription manifest is STRONGLY discouraged.',
        'This action should only be taken for debugging purposes.',
    ]
    org = target_sat.api.Organization().create()
    _, temporary_local_manifest_path = mkstemp(prefix='manifest-', suffix='.zip')
    with (
        function_sca_manifest as manifest,
        open(temporary_local_manifest_path, 'wb') as file_handler,
    ):
        file_handler.write(manifest.content)
    with session:
        session.organization.select(org.name)
        # Ignore "Danger alert: Katello::Errors::UpstreamConsumerNotFound'" as server will connect
        # to upstream subscription service to verify
        # the consumer uuid, that will be displayed in flash error messages
        # Note: this happen only when using clone manifest.
        session.subscription.add_manifest(
            temporary_local_manifest_path,
            ignore_error_messages=['Danger alert: Katello::Errors::UpstreamConsumerNotFound'],
        )
        assert session.subscription.has_manifest
        subscriptions = session.subscription.read_subscriptions()
        assert len(subscriptions) >= 1
        assert any('Red Hat' in subscription['Name'] for subscription in subscriptions)
        assert int(subscriptions[0]['Entitlements']) > 0
        assert int(subscriptions[0]['Consumed']) >= 0
        # manifest delete testing
        delete_message = session.subscription.read_delete_manifest_message()
        assert ' '.join(expected_message_lines) == delete_message
        assert session.subscription.has_manifest
        session.subscription.delete_manifest(
            ignore_error_messages=['Danger alert: Katello::Errors::UpstreamConsumerNotFound']
        )
        assert not session.subscription.has_manifest
        # reimport manifest
        session.subscription.add_manifest(
            temporary_local_manifest_path,
            ignore_error_messages=['Danger alert: Katello::Errors::UpstreamConsumerNotFound'],
        )
        assert session.subscription.has_manifest
        results = target_sat.execute(
            'grep -E "NullPointerException|CandlepinError" /var/log/candlepin/candlepin.log'
        )
        assert results.stdout == ''


def test_positive_access_with_non_admin_user_without_manifest(test_name, target_sat):
    """Access subscription page with non admin user that has the necessary
    permissions to check that there is no manifest uploaded.

    :id: dab9dc15-39a8-4105-b7ff-ecef909dc6e6

    :expectedresults: Subscription page is rendered properly without errors

    :BZ: 1417082

    :CaseImportance: Critical
    """
    org = target_sat.api.Organization().create()
    role = target_sat.api.Role(organization=[org]).create()
    target_sat.api_factory.create_role_permissions(
        role,
        {
            'Katello::Subscription': [
                'view_subscriptions',
                'manage_subscription_allocations',
                'import_manifest',
                'delete_manifest',
            ],
            'Organization': ['view_organizations', 'edit_organizations'],
        },
    )
    user_password = gen_string('alphanumeric')
    user = target_sat.api.User(
        admin=False,
        role=[role],
        password=user_password,
        organization=[org],
        default_organization=org,
    ).create()
    with target_sat.ui_session(test_name, user=user.login, password=user_password) as session:
        assert not session.subscription.has_manifest


@pytest.mark.upgrade
def test_positive_access_with_non_admin_user_with_manifest(
    test_name, function_sca_manifest_org, target_sat
):
    """Access subscription page with user that has only view_subscriptions and view organizations
    permission and organization that has a manifest uploaded.

    :id: 9184fcf6-36be-42c8-984c-3c5d7834b3b4

    :expectedresults: Subscription page is rendered properly without errors
        and the default subscription is visible

    :BZ: 1417082, 1651981

    :customerscenario: true

    :CaseImportance: Critical
    """
    org = function_sca_manifest_org
    role = target_sat.api.Role(organization=[org]).create()
    target_sat.api_factory.create_role_permissions(
        role,
        {'Katello::Subscription': ['view_subscriptions'], 'Organization': ['view_organizations']},
    )
    user_password = gen_string('alphanumeric')
    user = target_sat.api.User(
        admin=False,
        role=[role],
        password=user_password,
        organization=[org],
        default_organization=org,
    ).create()
    with target_sat.ui_session(test_name, user=user.login, password=user_password) as session:
        assert (
            session.subscription.search(f'name = "{DEFAULT_SUBSCRIPTION_NAME}"')[0]['Name']
            == DEFAULT_SUBSCRIPTION_NAME
        )


def test_positive_access_manifest_as_another_admin_user(
    test_name, target_sat, function_sca_manifest
):
    """Other admin users should be able to access and manage a manifest
    uploaded by a different admin.

    :id: 02e319da-3b7a-4694-9164-475c2c71b9a8

    :expectedresults: Other admin user should see/manage the manifest

    :BZ: 1669241

    :customerscenario: true

    :CaseImportance: High
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
    with target_sat.ui_session(test_name, user=user1.login, password=user1_password) as session:
        target_sat.upload_manifest(org.id, function_sca_manifest.content)
        assert session.subscription.has_manifest
        # store subscriptions that have "Red Hat" in the name for later
        rh_subs = session.subscription.search("Red Hat")
    # try to view and delete the manifest with another admin
    with target_sat.ui_session(test_name, user=user2.login, password=user2_password) as session:
        assert session.subscription.has_manifest
        assert rh_subs == session.subscription.search("Red Hat")
        session.subscription.delete_manifest(
            ignore_error_messages=['Danger alert: Katello::Errors::UpstreamConsumerNotFound']
        )
        assert not session.subscription.has_manifest


def test_select_customizable_columns_uncheck_and_checks_all_checkboxes(
    session, function_org, function_sca_manifest
):
    """Ensures that no column headers from checkboxes show up in the table after
    unticking everything from selectable customizable column

    :id: 88e140c7-ab4b-4d85-85bd-d3eff12162d7

    :steps:
        1. Login and go to Content -> Subscription
        2. Click selectable customizable column icon next to search button
        3. Iterate through list of checkboxes
        4. Unchecks all ticked checkboxes
        5. Verify that the table header column is empty after filter
        6. Check all ticked checkboxes
        7. Verify that the table header column is the same as the Checkbox_dict

        Note: Table header will always contain 'Select all rows' header in html,
        but will not be displayed in UI

    :expectedresults:
        1. No column headers show up

    :CaseImportance: Medium
    """
    checkbox_dict = {
        'Name': False,
        'SKU': False,
        'Contract': False,
        'Start Date': False,
        'End Date': False,
        'Requires Virt-Who': False,
        'Type': False,
        'Consumed': False,
        'Entitlements': False,
        'Product Host Count': False,
    }
    org = function_org
    with session:
        session.organization.select(org.name)
        session.subscription.add_manifest(
            function_sca_manifest.path,
            ignore_error_messages=['Danger alert: Katello::Errors::UpstreamConsumerNotFound'],
        )
        headers = session.subscription.filter_columns(checkbox_dict)
        assert headers == ('Select all rows',)
        time.sleep(3)
        checkbox_dict.update((k, True) for k in checkbox_dict)
        col = session.subscription.filter_columns(checkbox_dict)
        checkbox_dict.update({'Select all rows': ''})
        assert set(col) == set(checkbox_dict)


@pytest.mark.parametrize('setting_update', ['expire_soon_days'], indirect=True)
def test_positive_check_manifest_validity_notification(
    target_sat, setting_update, function_org, function_sca_manifest
):
    """Check notification when manifest is going to expire.

    :id: 29ab0e80-25eb-44f0-9294-3a26922c33c5

    :setup:
        1. create new organization

    :steps:
        1. Upload expired manifest in newly created org
        2. Go to Content > Subscriptions page, click on 'Manage Manifest' button.
        3. Search for message string 'Manifest expired', or 'Your manifest expired'
        4. Delete expired manifest from this org (cleanup part)
        5. Upload non-expired manifest
        6. Go to Content > Subscription page, click on 'Manage Manifest' button.
        7. Search for message string 'Manifest expiring soon', or 'Your manifest will expire'
        8. Delete non-expired manifest from this org (cleanup part)

    :expectedresults:
        1. 'Manifest expired', 'Manifest expiring soon' messages appear on Manage Manifest modal box

    :Verifies: SAT-11630

    :customerscenario: true
    """
    remote_path = f'/tmp/{EXPIRED_MANIFEST}'
    target_sat.put(DataFile.EXPIRED_MANIFEST_FILE, remote_path)
    # upload expired manifest
    target_sat.cli.Subscription.upload({'organization-id': function_org.id, 'file': remote_path})

    with target_sat.ui_session() as session:
        # Message - Manifest expired
        session.organization.select(function_org.name)
        # read expire manifest message
        expired_manifest = session.subscription.read_subscription_manifest_header_message_and_date()
        assert 'Manifest expired' in expired_manifest['header'], 'Manifest expire alert not found'
        if not is_open('SAT-25052'):
            assert (
                f'Your manifest expired on {EXPIRED_MANIFEST_DATE}. To continue using '
                f'Red Hat content, import a new manifest.' in expired_manifest['message']
            )
        # Cleanup - delete expired manifest
        session.subscription.delete_manifest(
            ignore_error_messages=['Danger alert: Katello::Errors::UpstreamConsumerNotFound']
        )

        # Message - Manifest expiring soon
        # Upload non-expire manifest
        target_sat.upload_manifest(function_org.id, function_sca_manifest.content)

        # Initially 'Manifest expiring soon' message not found
        assert not session.subscription.is_subscription_manifest_header_message_display()
        # then update the 'Expire soon days' value from settings > Content
        # value should be greater than 365 to get expected output message
        setting_update.value = 366
        setting_update = setting_update.update({'value'})
        session.browser.refresh()
        # Predict expire date using below formula
        date = datetime.now() + timedelta(days=365)
        formatted_date = date.strftime('%a %b %d %Y')
        # read expire manifest message
        expiring_soon = session.subscription.read_subscription_manifest_header_message_and_date()
        assert 'Manifest expiring soon' in expiring_soon['header'], (
            'Manifest expire alert not found'
        )
        assert formatted_date in expiring_soon['date']
        session.subscription.refresh_manifest()
        expires_date = session.subscription.read_subscription_manifest_expiration_date_only()
        assert formatted_date in expires_date
        # Cleanup - delete non-expired manifest
        session.subscription.delete_manifest(
            ignore_error_messages=['Danger alert: Katello::Errors::UpstreamConsumerNotFound']
        )


def test_positive_populate_future_date_subcription(
    target_sat,
    function_org,
    func_future_dated_subscription_manifest,
):
    """Upload manifest which has future date subscription and verify future date subscription populated

    :id: 87683cfc-8e65-4392-a437-ad5d88f5f618

    :expectedresults:
        1. Future date subscription should populate in Subscription table

    :Verifies: SAT-29203

    :customerscenario: true
    """
    with target_sat.ui_session() as session:
        session.organization.select(function_org.name)
        assert session.subscription.has_manifest, 'Manifest not uploaded'

        # Get current date time and convert into date
        current_datetime = datetime.now(ZoneInfo(get_localzone_name()))
        current_date = current_datetime.date()

        # Get subscription Start Date and compare with current date
        subscriptions = session.subscription.read_subscriptions()
        if not any(
            datetime.strptime(sub['Start Date'], '%Y-%m-%d %H:%M:%S %Z').date() > current_date
            for sub in subscriptions
        ):
            raise AssertionError('Subscription start date is not in the future')

        # Delete the manifest from Organization
        session.subscription.delete_manifest(
            ignore_error_messages=['Danger alert: Katello::Errors::UpstreamConsumerNotFound']
        )
        assert not session.subscription.has_manifest, 'Manifest was not deleted'
