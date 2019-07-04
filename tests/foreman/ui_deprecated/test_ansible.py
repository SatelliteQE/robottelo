"""Tests for Ansible integration in UI

:Requirement: Ansible Integration

:CaseLevel: System

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""


from robottelo.decorators import (
    run_only_on,
    stubbed,
    tier1,
    tier3,
    tier4,
    upgrade
)
from robottelo.test import UITestCase


class AnsibleTestCase(UITestCase):
    """Implements Ansible integration tests in UI"""

    @run_only_on('sat')
    @stubbed()
    @tier4
    def test_positive_install_ansible_plugin(self):
        """Install Ansible plugin in Satellite

        :id: 88b5bad8-7d15-4286-a70e-0c7125a0de39

        :steps: Install Ansible plugin in Satellite by running
            `satellite-installer` using `--enable-foreman-plugin-ansible`
            option

        :expectedresults: Ansible plugin is installed successfully. This can be
            verified by editing any host and checking the presence of `Ansible
            Roles` tab.

        :caseautomation: notautomated

        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_setup_ansible_callback_satellite_host(self):
        """Setup Ansible callback when Ansible is installed in the Satellite
        host

        :id: d9296383-66f8-4999-9102-ef28aff77877

        :steps: Follow the Ansible callback setup steps mentioned in
            https://theforeman.org/plugins/foreman_ansible/1.x/index.html
            #2.1Ansiblecallback

        :expectedresults: Ansible callback is setup successfully. This can be
            verified by running Ansible setup module in any of the hosts.

        :caseautomation: notautomated

        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_setup_ansible_callback_capsule(self):
        """Setup Ansible callback when Ansible is installed in the Capsule

        :id: 72dec524-268e-480a-b7c1-6df2ebbe0d43

        :steps: Follow the Ansible callback setup steps mentioned in
            https://theforeman.org/plugins/foreman_ansible/1.x/index.html
            #2.1Ansiblecallback


        :expectedresults: Ansible callback is setup successfully. This can be
            verified by running Ansible setup module in any of the hosts.

        :caseautomation: notautomated

        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_tower_installed_in_satellite_host(self):
        """Generate Ansible run reports when Ansible Tower is installed in the
        Satellite host

        :id: 45d1f7e2-1071-432c-a6cc-7757a26ca2e4

        :steps:

            1. Install Ansible Tower in the Satellite host
            2. Setup Ansible callback in the Tower
            3. Run Ansible setup module

        :expectedresults: Ansible Tower is integrated with Satellite and the
            Ansible run reports are shown in Satellite.

        :caseautomation: notautomated

        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_tower_installed_in_capsule(self):
        """Check Ansible runs when Ansible Tower is installed in the Capsule

        :id: 5af34b23-b6d7-49f5-9e92-ac0ba2182c86

        :steps:

            1. Install Ansible Tower in the Capsule
            2. Setup Ansible callback in the Tower
            3. Run Ansible setup module

        :expectedresults: Ansible Tower is integrated with Satellite and the
            Ansible run reports are shown in Satellite.

        :caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_playbook_run_report_host_already_present(self):
        """Ansible report creation for a host which is already present in
        Satellite

        :id: 334dfe58-6019-4d20-ab29-8cc002422ce6

        :steps:

            1. Register a host to Satellite
            2. Run Ansible on the host

        :expectedresults: Ansible report is created for the host

        :caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_playbook_run_report_host_not_present(self):
        """Ansible report creation for a host which is not present in
        Satellite

        :id: 7f6f5767-3967-4741-9021-ce09ad69926a

        :steps: Run Ansible on a host not registered to Satellite yet

        :expectedresults: The host is created in Satellite and the Ansible
            report is created for the host

        :caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    @upgrade
    def test_positive_associate_ansible_roles_to_hosts(self):
        """Associate Ansible roles to hosts

        :id: 64839064-20ac-45ea-b8ba-c778df74ba47

        :steps:
            1. From Web UI -> Hosts -> Select a Host -> Edit -> Ansible Roles
                -> Select the required Ansible roles -> Click Submit.
            2. Run the associated Ansible roles in the hosts.

        :expectedresults:

            1. The Ansible roles are associated to the appropriate hosts
            2. The Ansible run reports generated

        :caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    @upgrade
    def test_positive_execute_custom_ansible_role(self):
        """Execute custom Ansible roles on hosts

        :id: 39bc81fd-2b6c-4dac-8db7-38312ba9bffb

        :steps:

            1. On Satellite server create a new custom Ansible role.  A role
                with a single task writing a new file on client host, can be
                created using a template like.  "echo 'task: shell: touch
                /tmp/file.test' > /etc/ansible/roles/custom/"
            2. From Web UI -> Hosts -> Select a Host -> Edit -> Ansible Roles
                -> Select the new custom Ansible role -> Click Submit.
            3. Run the associated Ansible role in the host.

        :expectedresults:

            1. The custom role are available in Satellite.
            2. The Ansible roles are associated to the appropriate hosts.
            3. The Ansible run reports generated.
            4. The role task has been performed successfully in the client host
               (ssh in to the client host and check that /tmp/file.test exists)

        :caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_associate_ansible_roles_to_hostgroups(self):
        """Associate Ansible roles to hostgroups

        :id: 685ce52d-5684-49b6-ace6-ede253a58b24

        :steps:

            1. From Web UI -> Configure -> Host groups -> Select a Host group
                -> Ansible Roles -> Select the required Ansible roles -> Click
                Submit
            2. Provision a host with the Host group from above

        :expectedresults:

            1. The Ansible role is associated to the appropriate Host group
            2. The Ansible run reports generated

        :caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_run_ansibles_role_one_host(self):
        """Check if Ansible roles can be run on one host

        :id: ab40f3ae-7dc3-47d1-b5e6-18ca1f1d5460

        :expectedresults: Ansibles roles ran successfully on the host and the
            reports generated

        :caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    @upgrade
    def test_positive_run_ansibles_role_multiple_hosts(self):
        """Check if Ansible roles can be run on multiple hosts

        :id: 349b8bd8-7fd6-482a-99d2-641ac319f44f

        :steps: From Web UI -> Hosts -> Select multiple hosts -> Select Action
            -> Play Ansible Roles

        :expectedresults: Ansibles roles ran successfully on multiple hosts

        :caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_permission_view_ansible_roles(self):
        """Check if an user with view_ansible_roles permission able to view
        the Ansible roles

        :id: 60aa2d5a-571c-40af-bfaf-ca406b6a4672

        :expectedresults: An user with view_ansible_roles permission is able to
            view the Ansible roles.

        :caseautomation: notautomated

        :caselevel: Acceptance

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_permission_import_ansible_roles(self):
        """Check if an user with import_ansible_roles permission able to
        import Ansible roles

        :id: f5939207-66ea-4b3c-8c8a-46a588b79026

        :expectedresults: An user with import_ansible_roles permission is able
            to import Ansible roles.

        :caseautomation: notautomated

        :caselevel: Acceptance


        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_permission_destroy_ansible_roles(self):
        """Check if an user with destroy_ansible_roles permission able to
        delete Ansible roles

        :id: e9c3df3f-3a03-4665-a0f7-184212b73e74

        :expectedresults: An user with destroy_ansible_roles permission is able
            to delete Ansible roles

        :caseautomation: notautomated

        :caselevel: Acceptance


        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_permission_play_roles(self):
        """Check if an user with play_roles permission able to run the Ansible
        roles

        :id: 14948966-4ee0-44c6-9de0-6b98ef11dc62

        :expectedresults: The user with play_roles permission is able to run
            the Ansible roles

        :caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_permission_play_multiple_roles(self):
        """Check if an user with play_multiple_roles permission able to run
        multiple Ansible roles

        :id: 33cedeb4-c2e9-4771-b333-f5cbf98cfbf1

        :expectedresults: The user with play_multiple_roles permission is able
            to run multiple Ansible roles

        :caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_permissions(self):
        """Check if an user without appropriate Ansible permissions is
        prevented from using Ansible actions

        :id: ac4a5d48-01c8-4e4a-8fa2-f054965880a1

        :steps: Make sure that the user does not have the following
            permissions:

            * view_ansible_roles
            * import_ansible_roles
            * destroy_ansible_roles
            * play_roles
            * play_multiple_roles

        :expectedresults: The user is not able to:

            * View Ansible roles
            * Import Ansible roles
            * Delete Ansible roles
            * Run roles
            * Run multiple roles

        :caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_add_ansible_parameter_to_host(self):
        """Check if an Ansible parameter can be added to a host

        :id: 79395d8d-599e-4330-9f9f-40ef6762510d

        :expectedresults: Ansible parameter added to the host successfully

        :caseautomation: notautomated

        :caselevel: Acceptance


        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_add_ansible_parameter_to_hostgroup(self):
        """Check if an Ansible parameter can be added to a hostgroup

        :id: f05f599e-947f-4500-b550-99a93948c7ed

        :expectedresults: Ansible parameter added to the hostgroup successfully

        :caseautomation: notautomated

        :caselevel: Acceptance


        :CaseImportance: Critical
        """

    @stubbed()
    @tier3
    def test_positive_update_inventory_with_groups(self):
        """Tower inventory should be updated with sat groups like host-group,
        location, organization, content-views and life-cycle environment
        with admin user.

        :id: 48a1eba3-4297-4778-8bde-b667c3ac40f0

        :Setup:

            1. Ansible Tower should be installed w/th valid license
            2. Satellite server should be configured w/ groups like:
                host-group, location, organization, content-views and
                life-cycle environment

        :Steps:

            1. Add credentials by specifying type, URL, Username(admin) and
                password of Satellite6
            2. Goto Inventories -> Add inventory
            3. Add group and Source should be Satellite6
            4. Select the added credentials in step1 and click 'save'.

        :expectedresults: Tower inventory should show sat groups

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_update_inventory_with_normal_user(self):
        """Tower inventory should be updated with sat groups like host-group,
        location, organization, content-views and life-cycle environment
        accessible to non-admin sat user.

        :id: dddf4881-da3b-4254-b782-31632dd9b4ef

        :Setup:

            1. Ansible Tower should be installed w/th valid license
            2. Satellite server should be configured w/ groups like:
                host-group, location, organization, content-views and
                life-cycle environment
            3. A normal user should be defined w/ some roles and filters

        :Steps:

            1. Add credentials by specifying type, URL, user name(non-admin)
                and password of Satellite6
            2. Goto Inventories -> Add inventory
            3. Add group and Source should be Satellite6
            4. Select the added credentials in step1 and click 'save'.

        :expectedresults: Tower inventory should show sat groups accessible to
            non-admin sat user

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_run_job_on_sat_hosts(self):
        """Run playbooks on the existing satellite hosts in tower through
        Ansible job templates

        :id: a46bdd3a-9012-41eb-a67f-15496b30870d

        :Setup:

            1. Ansible Tower should be installed w/th valid license
            2. Inventory should be configured w/ sat6 server

        :Steps:

            1. Add ansible scripts or playbook to run on selected inventory
            2. Add ansible job template and select inventory, job template

        :expectedresults: Playbook associated to Job template should run on all
            associated sat hosts in selected inventory

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    @upgrade
    def test_positive_provision_with_provisioning_callback(self):
        """Host provisioned through satellite should be able to run playbook
        itself from Tower through provisioning callback.

        :id: 722e8460-7156-4fc6-8dad-3ec1bdea2c6c

        :Setup:

            1. Ansible Tower should be installed w/th valid license
            2. Inventory should be configured w/ sat6 server
            3. Provisioning callback should be enabled in Tower
            4. Satellite should be updated w/ required changes in templates
                and global variables.

        :expectedresults: Playbook associated to Job template should run on the
            host during post install phase.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_provisioning_callback_with_imagebased(self):
        """Host provisioned through satellite should be able to run playbook
        itself from Tower through provisioning callback using image based
        provisioning.

        :id: 153e67bb-65de-4fc6-bd8a-b910526b71e4

        :Setup:

            1. Ansible Tower should be installed w/th valid license
            2. Inventory should be configured w/ sat6 server
            3. Provisioning callback should be enabled in Tower
            4. Satellite should be updated w/ required changes in templates
                and global variables.

        :expectedresults: Playbook associated to Job template should run on the
            host during post install phase.

        :caseautomation: notautomated

        :CaseLevel: System
        """
