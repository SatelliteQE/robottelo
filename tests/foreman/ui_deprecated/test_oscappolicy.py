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

from robottelo.config import settings
from robottelo.constants import (
    OSCAP_PERIOD,
    OSCAP_PROFILE,
    OSCAP_WEEKDAY,
)
from robottelo.datafactory import invalid_values_list, valid_data_list
from robottelo.decorators import (
    skip_if_not_set,
    tier1,
    upgrade
)
from robottelo.helpers import get_data_file
from robottelo.test import UITestCase
from robottelo.ui.factory import (
    make_oscapcontent,
    make_oscappolicy,
)
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
