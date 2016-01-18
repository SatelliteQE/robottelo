from fauxfactory import gen_string
from robottelo.config import settings
from robottelo.constants import (
    OSCAP_PERIOD,
    OSCAP_PROFILE,
    OSCAP_WEEKDAY,
)
from robottelo.datafactory import invalid_values_list, valid_data_list
from robottelo.decorators import skip_if_bug_open, tier1
from robottelo.helpers import get_data_file
from robottelo.test import UITestCase
from robottelo.ui.factory import make_oscapcontent, make_oscappolicy
from robottelo.ui.session import Session


class OpenScapPolicy(UITestCase):
    """Implements Oscap Policy tests in UI."""

    @classmethod
    def setUpClass(cls):
        super(OpenScapPolicy, cls).setUpClass()
        cls.content_path = get_data_file(
            settings.oscap.content_path
        )

    @tier1
    def test_positive_create_with_policy_name(self):
        """Create OpenScap Policy.

        @Feature: OpenScap Policy - Positive Create.

        @Steps:

        1. Create an openscap content.
        2. Create an openscap Policy.
        3. Provide all the appropriate parameters.

        @Assert: Whether creating  Policy for OpenScap is successful.
        """
        content_name = gen_string('alpha')
        with Session(self.browser) as session:
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
                        profile=OSCAP_PROFILE['rhccp'],
                        period_value=OSCAP_WEEKDAY['friday'],
                    )
                    self.assertIsNotNone(
                        self.oscappolicy.search(policy_name))

    @tier1
    def test_positive_delete_by_policy_name(self):
        """Create OpenScap Policy.

        @Feature: OpenScap Policy - Positive Create.

        @Steps:

        1. Create an openscap content.
        2. Create an openscap Policy.
        3. Provide all the appropriate parameters.
        4. Delete the openscap Policy.

        @Assert: Whether deleting  Policy for OpenScap is successful.
        """
        content_name = gen_string('alpha')
        with Session(self.browser) as session:
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
                        profile=OSCAP_PROFILE['rhccp'],
                        period_value=OSCAP_WEEKDAY['friday'],
                    )
                    self.assertIsNotNone(
                        self.oscappolicy.search(policy_name))
                    self.oscappolicy.delete(policy_name)

    @skip_if_bug_open('bugzilla', 1293296)
    @tier1
    def test_negative_create_with_invalid_name(self):
        """Create OpenScap Policy with negative values.

        @Feature: OpenScap Policy - Negative Create.

        @Steps:

        1. Create an openscap content.
        2. Create an openscap Policy.
        3. Provide all the appropriate parameters.

        @Assert: Creating  Policy for OpenScap is not successful.

        @BZ: 1293296
        """
        content_name = gen_string('alpha')
        with Session(self.browser) as session:
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
                        profile=OSCAP_PROFILE['rhccp'],
                        period_value=OSCAP_WEEKDAY['friday'],
                    )
                    self.assertIsNone(self.oscappolicy.search(policy_name))

    @tier1
    def test_positive_update(self):
        """Update OpenScap Policy.

        @Feature: OpenScap Policy - Positive Update.

        @Steps:

        1. Create an openscap content.
        2. Create an openscap Policy.
        3. Provide all the appropriate parameters.
        4. Update openscap policy with valid values.

        @Assert: Updating Policy for OpenScap is successful.
        """
        content_name = gen_string('alpha')
        policy_name = gen_string('alpha')
        with Session(self.browser) as session:
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
                profile=OSCAP_PROFILE['rhccp'],
                period_value=OSCAP_WEEKDAY['friday'],
            )
            self.assertIsNotNone(
                self.oscappolicy.search(policy_name))
            for new_policy_name in invalid_values_list(interface='ui'):
                with self.subTest(new_policy_name):
                    self.oscappolicy.update(
                        name=policy_name,
                        new_name=new_policy_name,
                        content=content_name,
                        profile=OSCAP_PROFILE['usgcb'],
                        period=OSCAP_PERIOD['weekly'],
                        period_value=OSCAP_WEEKDAY['sunday'],
                    )
                    self.assertIsNotNone(
                        self.oscappolicy.search(new_policy_name))
                    policy_name = new_policy_name
