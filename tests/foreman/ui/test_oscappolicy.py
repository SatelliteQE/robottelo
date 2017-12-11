"""Tests for Oscappolicy

:Requirement: Oscappolicy

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_string
from nailgun import entities

from robottelo.api.utils import promote
from robottelo.config import settings
from robottelo.constants import (
    ANY_CONTEXT,
    OSCAP_PERIOD,
    OSCAP_PROFILE,
    OSCAP_WEEKDAY,
)
from robottelo.datafactory import invalid_values_list, valid_data_list
from robottelo.decorators import (
    skip_if_not_set,
    tier1,
    tier2,
    upgrade
)
from robottelo.helpers import get_data_file
from robottelo.test import UITestCase
from robottelo.ui.factory import (
    make_oscapcontent,
    make_oscappolicy,
    set_context
)
from robottelo.ui.locators import locators
from robottelo.ui.session import Session


class OpenScapPolicy(UITestCase):
    """Implements Oscap Policy tests in UI."""

    @classmethod
    @skip_if_not_set('oscap')
    def setUpClass(cls):
        super(OpenScapPolicy, cls).setUpClass()
        cls.content_path = get_data_file(
            settings.oscap.content_path
        )

    @tier1
    def test_positive_create_with_policy_name(self):
        """Create OpenScap Policy.

        :id: cdf2bc8c-ce60-4d49-b4e9-9acbf1192bc2

        :Steps:

            1. Create an openscap content.
            2. Create an openscap Policy.
            3. Provide all the appropriate parameters.

        :expectedresults: Whether creating  Policy for OpenScap is successful.

        :CaseImportance: Critical
        """
        content_name = gen_string('alpha')
        with Session(self) as session:
            make_oscapcontent(
                session,
                name=content_name,
                content_path=self.content_path,
            )
            self.assertIsNotNone(
                self.oscapcontent.search(content_name))
            for policy_name in valid_data_list():
                with self.subTest(policy_name):
                    make_oscappolicy(
                        session,
                        content=content_name,
                        name=policy_name,
                        period=OSCAP_PERIOD['weekly'],
                        profile=OSCAP_PROFILE['c2s_rhel6'],
                        period_value=OSCAP_WEEKDAY['friday'],
                    )
                    self.assertIsNotNone(
                        self.oscappolicy.search(policy_name))

    @tier2
    def test_positive_check_dashboard(self):
        """Create OpenScap Policy which is connected to the host. That policy
        dashboard should be rendered and correctly display information about
        the host

        :id: 3c1575cb-f290-4d99-bb86-61b9ca6a62eb

        :Steps:

            1. Create new host group
            2. Create new host using host group from step 1
            3. Create an openscap content.
            4. Create an openscap Policy using host group from step 1

        :expectedresults: Policy dashboard rendered properly and has necessary
            data

        :BZ: 1424936

        :CaseLevel: Integration

        :CaseImportance: Critical
        """
        content_name = gen_string('alpha')
        policy_name = gen_string('alpha')

        org = entities.Organization().create()
        lce = entities.LifecycleEnvironment(organization=org).create()
        content_view = entities.ContentView(organization=org).create()
        content_view.publish()
        content_view = content_view.read()
        promote(content_view.version[0], environment_id=lce.id)
        loc = entities.Location(organization=[org]).create()
        hostgroup = entities.HostGroup(
            location=[loc],
            organization=[org],
        ).create()
        entities.Host(
            hostgroup=hostgroup,
            location=loc,
            organization=org,
            content_facet_attributes={
                'content_view_id': content_view.id,
                'lifecycle_environment_id': lce.id,
            },
        ).create()

        with Session(self) as session:
            set_context(session, org=ANY_CONTEXT['org'])
            make_oscapcontent(
                session,
                name=content_name,
                content_path=self.content_path,
            )
            self.assertIsNotNone(
                self.oscapcontent.search(content_name))
            make_oscappolicy(
                session,
                content=content_name,
                name=policy_name,
                period=OSCAP_PERIOD['weekly'],
                profile=OSCAP_PROFILE['c2s_rhel6'],
                period_value=OSCAP_WEEKDAY['friday'],
                org=org.name,
                loc=loc.name,
                host_group=hostgroup.name,
            )
            self.oscappolicy.search_and_click(policy_name)
            self.assertEqual(self.dashboard.get_total_hosts_count(), 1)
            self.assertEqual(
                self.oscappolicy.wait_until_element(
                    locators[
                        'dashboard.hcc.hosts_percentage'
                    ] % 'Not audited').text,
                '100%'
            )

    @tier1
    @upgrade
    def test_positive_delete_by_policy_name(self):
        """Create OpenScap Policy.

        :id: 7497aad0-1e2f-426e-928d-72e430a0e853

        :Steps:

            1. Create an openscap content.
            2. Create an openscap Policy.
            3. Provide all the appropriate parameters.
            4. Delete the openscap Policy.

        :expectedresults: Whether deleting  Policy for OpenScap is successful.

        :CaseImportance: Critical
        """
        content_name = gen_string('alpha')
        with Session(self) as session:
            make_oscapcontent(
                session,
                name=content_name,
                content_path=self.content_path,
            )
            self.assertIsNotNone(
                self.oscapcontent.search(content_name))
            for policy_name in valid_data_list():
                with self.subTest(policy_name):
                    make_oscappolicy(
                        session,
                        content=content_name,
                        name=policy_name,
                        period=OSCAP_PERIOD['weekly'],
                        profile=OSCAP_PROFILE['c2s_rhel6'],
                        period_value=OSCAP_WEEKDAY['friday'],
                    )
                    self.assertIsNotNone(
                        self.oscappolicy.search(policy_name))
                    self.oscappolicy.delete(policy_name, dropdown_present=True)

    @tier1
    def test_negative_create_with_invalid_name(self):
        """Create OpenScap Policy with negative values.

        :id: dfebf26b-194f-473d-b5a6-9061c520f57e

        :Steps:

            1. Create an openscap content.
            2. Create an openscap Policy.
            3. Provide all the appropriate parameters.

        :expectedresults: Creating  Policy for OpenScap is not successful.

        :BZ: 1293296

        :CaseImportance: Critical
        """
        content_name = gen_string('alpha')
        with Session(self) as session:
            make_oscapcontent(
                session,
                name=content_name,
                content_path=self.content_path,
            )
            self.assertIsNotNone(
                self.oscapcontent.search(content_name))
            for policy_name in invalid_values_list(interface='ui'):
                with self.subTest(policy_name):
                    make_oscappolicy(
                        session,
                        content=content_name,
                        name=policy_name,
                        period=OSCAP_PERIOD['weekly'],
                        profile=OSCAP_PROFILE['c2s_rhel6'],
                        period_value=OSCAP_WEEKDAY['friday'],
                    )
                    self.assertIsNone(self.oscappolicy.search(policy_name))

    @tier1
    def test_positive_update(self):
        """Update OpenScap Policy.

        :id: 58392782-ab25-4c12-aebc-adf23c5d9d43

        :Steps:

            1. Create an openscap content.
            2. Create an openscap Policy.
            3. Provide all the appropriate parameters.
            4. Update openscap policy with valid values.

        :expectedresults: Updating Policy for OpenScap is successful.

        :CaseImportance: Critical
        """
        content_name = gen_string('alpha')
        policy_name = gen_string('alpha')
        with Session(self) as session:
            make_oscapcontent(
                session,
                name=content_name,
                content_path=self.content_path,
            )
            self.assertIsNotNone(
                self.oscapcontent.search(content_name))
            make_oscappolicy(
                session,
                content=content_name,
                name=policy_name,
                period=OSCAP_PERIOD['weekly'],
                profile=OSCAP_PROFILE['c2s_rhel6'],
                period_value=OSCAP_WEEKDAY['friday'],
            )
            self.assertIsNotNone(
                self.oscappolicy.search(policy_name))
            for new_policy_name in valid_data_list():
                with self.subTest(new_policy_name):
                    self.oscappolicy.update(
                        name=policy_name,
                        new_name=new_policy_name,
                        content=content_name,
                        profile=OSCAP_PROFILE['esp'],
                        period=OSCAP_PERIOD['weekly'],
                        period_value=OSCAP_WEEKDAY['sunday'],
                    )
                    self.assertIsNotNone(
                        self.oscappolicy.search(new_policy_name))
                    policy_name = new_policy_name

    @tier1
    def test_positive_create_with_space_policy_name(self):
        """Create OpenScap Policy with a space in its name.

        :id: a45ec231-0ca9-4719-9239-eef0355822dc

        :Steps:

            1. Create an openscap content.
            2. Create an openscap Policy.
            3. Provide openscap policy name with space in it.
            4. Provide all other the appropriate parameters.

        :expectedresults: Creation of Policy with a space in its name is
            successful.

        :BZ: 1292622

        :CaseImportance: Critical
        """
        content_name = gen_string('alpha')
        with Session(self) as session:
            make_oscapcontent(
                session,
                name=content_name,
                content_path=self.content_path,
            )
            self.assertIsNotNone(
                self.oscapcontent.search(content_name))
            policy_name = "Test policy"
            with self.subTest(policy_name):
                make_oscappolicy(
                    session,
                    content=content_name,
                    name=policy_name,
                    period=OSCAP_PERIOD['weekly'],
                    profile=OSCAP_PROFILE['c2s_rhel6'],
                    period_value=OSCAP_WEEKDAY['friday'],
                )
                self.assertIsNotNone(
                    self.oscappolicy.search(policy_name))
