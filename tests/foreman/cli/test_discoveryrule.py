# -*- encoding: utf-8 -*-
"""Test class for Foreman Discovery Rules

@Requirement: Discoveryrule

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: CLI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""

from robottelo.decorators import (
    run_only_on,
    tier1,
    tier2,
    stubbed,
)
from robottelo.test import CLITestCase


class DiscoveryRuleTestCase(CLITestCase):
    """Implements Foreman discovery Rules tests in CLI."""

    @run_only_on('sat')
    @stubbed
    @tier1
    def test_positive_create_with_name(self):
        """Create Discovery Rule using different names

        @id: 066e66bc-c572-4ae9-b458-90daf83bab54

        @Assert: Rule should be successfully created

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed
    @tier1
    def test_positive_create_with_search(self):
        """Create Discovery Rule using different search queries

        @id: 2383e898-a968-4183-a270-55e9350e0596

        @Assert: Rule should be successfully created and has expected search
        value

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed
    @tier1
    def test_positive_create_with_hostname(self):
        """Create Discovery Rule using valid hostname

        @id: deee22c3-dcfd-4940-b27c-cca137ec9a92

        @Assert: Rule should be successfully created and has expected hostname
        value

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed
    @tier1
    def test_positive_create_with_org_loc_name(self):
        """Create discovery rule by associating org and location names

        @id: f0d550ae-16d8-48ec-817e-d2e5b7405b46

        @Assert: Rule was created and with given org & location names.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed
    @tier1
    def test_positive_create_with_org_loc_id(self):
        """Create discovery rule by associating org and location ids.

        @id: 8b7411b8-bb4b-483e-837b-c468620ff99b

        @Assert: Rule was created and with given org & location ids.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed
    @tier1
    def test_positive_create_with_hosts_limit(self):
        """Create Discovery Rule providing any number from range 1..100 for
        hosts limit option

        @id: c28422c2-1f6a-4045-b722-f9f9d864e963

        @Assert: Rule should be successfully created and has expected hosts
        limit value

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed
    @tier1
    def test_positive_create_with_max_count(self):
        """Create Discovery Rule providing any number from range 1..100 for
        max count option

        @id: 590ca353-d3d7-4700-be34-13de00f46276

        @Assert: Rule should be successfully created and has max_count set
        as per given value

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed
    @tier1
    def test_positive_create_with_priority(self):
        """Create Discovery Rule providing any number from range 1..100 for
        priority option

        @id: 8ef58279-0ad3-41a4-b8dd-65594afdb655

        @Assert: Rule should be successfully created and has expected priority
        value

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed
    @tier1
    def test_positive_create_disabled_rule(self):
        """Create Discovery Rule in disabled state

        @id: 8837a0c6-e19a-4c33-8b87-07b6f69dbb0f

        @Assert: Disabled rule should be successfully created

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed
    @tier1
    def test_negative_create_with_invalid_name(self):
        """Create Discovery Rule with invalid names

        @id: a0350dc9-8f5b-4673-be88-a5e35d1f8ca7

        @Assert: Error should be raised and rule should not be created

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed
    @tier1
    def test_negative_create_with_invalid_hostname(self):
        """Create Discovery Rule with invalid hostname

        @id: 0ae51085-30d0-44f9-9e49-abe928a8a4b7

        @Assert: Error should be raised and rule should not be created

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed
    @tier1
    def test_negative_create_with_too_long_limit(self):
        """Create Discovery Rule with too long host limit value

        @id: 12dbb023-c963-4ead-a81e-ad53033de947

        @Assert: Validation error should be raised and rule should not be
        created

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed
    @tier1
    def test_negative_create_with_same_name(self):
        """Create Discovery Rule with name that already exists

        @id: 5a914e76-de01-406d-9860-0e4e1521b074

        @Assert: Error should be raised and rule should not be created

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed
    @tier1
    def test_positive_delete(self):
        """Delete existing Discovery Rule

        @id: c9b88a94-13c4-496f-a5c1-c088187250dc

        @Assert: Rule should be successfully deleted

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed
    @tier1
    def test_positive_update_name(self):
        """Update discovery rule name

        @id: 1045e2c4-e1f7-42c9-95f7-488fc79bf70b

        @Assert: Rule name is updated

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed
    @tier2
    def test_positive_update_org_loc(self):
        """Update org and location of selected discovery rule

        @id: 26da79aa-30e5-4052-98ae-141de071a68a

        @Assert: Rule was updated and with given org & location.

        @caseautomation: notautomated

        @CaseLevel: Integration
        """

    @run_only_on('sat')
    @stubbed
    @tier1
    def test_positive_update_query(self):
        """Update discovery rule search query

        @id: 86943095-acc5-40ff-8e3c-88c76b36333d

        @Assert: Rule search field is updated

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed
    @tier1
    def test_positive_update_hostgroup(self):
        """Update discovery rule host group

        @id: 07992a3f-2aa9-4e45-b2e8-ef3d2f255292

        @Assert: Rule host group is updated

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed
    @tier1
    def test_positive_update_hostname(self):
        """Update discovery rule hostname value

        @id: 4c123488-92df-42f6-afe3-8a88cd90ffc2

        @Assert: Rule host name is updated

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed
    @tier1
    def test_positive_update_limit(self):
        """Update discovery rule limit value

        @id: efa6f5bc-4d56-4449-90f5-330affbcfb09

        @Assert: Rule host limit field is updated

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed
    @tier1
    def test_positive_update_priority(self):
        """Update discovery rule priority value

        @id: 0543cc73-c692-4bbf-818b-37353ec98986

        @Assert: Rule priority is updated

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed
    @tier1
    def test_positive_update_disable_enable(self):
        """Update discovery rule enabled state. (Disabled->Enabled)

        @id: 64e8b21b-2ab0-49c3-a12d-02dbdb36647a

        @Assert: Rule is successfully enabled

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed
    @tier1
    def test_negative_update_name(self):
        """Update discovery rule name using invalid names only

        @id: 8293cc6a-d983-460a-b76e-221ad02b54b7

        @Assert: Rule name is not updated

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed
    @tier1
    def test_negative_update_hostname(self):
        """Update discovery rule host name using number as a value

        @id: c382dbc7-9509-4060-9038-1617f7fef038

        @Assert: Rule host name is not updated

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed
    @tier1
    def test_negative_update_limit(self):
        """Update discovery rule host limit using invalid values

        @id: e3257d8a-91b9-406f-bd74-0fd1fb05bb77

        @Assert: Rule host limit is not updated

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed
    @tier1
    def test_negative_update_priority(self):
        """Update discovery rule priority using invalid values

        @id: 0778dd00-aa19-4062-bdf3-752e1b546ec2

        @Assert: Rule priority is not updated

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed
    @tier2
    def test_positive_create_rule_with_non_admin_user(self):
        """Create rule with non-admin user by associating discovery_manager role

        @id: 056535aa-3338-4c1e-8a4b-ebfc8bd6e456

        @Assert: Rule should be created successfully.

        @caseautomation: notautomated

        @CaseLevel: Integration
        """

    @run_only_on('sat')
    @stubbed
    @tier2
    def test_positive_delete_rule_with_non_admin_user(self):
        """Delete rule with non-admin user by associating discovery_manager role

        @id: 87ab969b-7d92-478d-a5c0-1c0d50e9bdd6

        @Assert: Rule should be deleted successfully.

        @caseautomation: notautomated

        @CaseLevel: Integration
        """

    @run_only_on('sat')
    @stubbed
    @tier2
    def test_positive_view_existing_rule_with_non_admin_user(self):
        """Existing rule should be viewed to non-admin user by associating
        discovery_reader role.

        @id: 7b1d90b9-fc2d-4ccb-93d3-605c2da876f7

        @Steps:

        1. create a rule with admin user
        2. create a non-admin user and assign 'Discovery Reader' role
        3. Login with non-admin user

        @Assert: Rule should be visible to non-admin user.

        @caseautomation: notautomated

        @CaseLevel: Integration
        """

    @run_only_on('sat')
    @stubbed
    @tier2
    def test_negative_delete_rule_with_non_admin_user(self):
        """Delete rule with non-admin user by associating discovery_reader role

        @id: f7f9569b-916e-46f3-bd89-a05e33483741

        @Assert: User should validation error and rule should not be deleted
        successfully.

        @caseautomation: notautomated

        @CaseLevel: Integration
        """
