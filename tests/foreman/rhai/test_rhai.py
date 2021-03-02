"""Tests for Red Hat Access Insights

:Requirement: Rhai

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: RHCloud-Insights

:Assignee: jpathan

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import csv

import pytest
import yaml
from airgun.entities.rhai.base import InsightsOrganizationPageError
from fauxfactory import gen_string

from robottelo.constants import ANY_CONTEXT


pytestmark = pytest.mark.usefixtures('attach_subscription')

NAV_ITEMS = [
    ('insightsaction', 'Details'),
    ('insightsinventory', 'All'),
    ('insightsoverview', 'Details'),
    ('insightsplan', 'All'),
    ('insightsrule', 'All'),
]


def test_positive_register_client_to_insights(vm, autosession):
    """Verify registration via insights-client.

    :id: 9815151e-d50d-4160-9d29-ae7c89422e18

    :expectedresults: Client should appear in Insights > Inventory.
    """
    table = autosession.insightsinventory.search(vm.hostname)
    assert table[0]['System Name'].text == vm.hostname


@pytest.mark.stubbed
def test_positive_register_client_with_template():
    """Register an insights client using the Global Registration Template.

    :id: c7664d22-e86d-470d-a4ee-4291e767c60c

    :expectedresults: Registered client should appear in the Insights > Systems

    :Steps:
        0. Import manifest, then enable and sync rhel-7-server-rpms x86_64 7Server (required for
           insights-client rpm).
        1. Create an activation key and associate it with the synced repository.
        2. In the Satellite web UI, navigate to Hosts > Provisioning Templates, find the Linux
           registration default template and click it. Click the Association tab.
        3. Ensure that the operating system that you want to register is in the Selected items
           column. Click Submit.
        4. Navigate to Hosts > Operating Systems and click the operating system that you want to
           register. Click the Templates tab.
        5. From the Registration template list, ensure that Linux registration default is
           selected. Click Submit.
        6. Navigate to Hosts > All Hosts > Register Host.
        7. From the Operating System list, select the operating system of hosts that you want to
           register.
        8. From the Insights list, select to register the hosts to Insights.
        9. In the Activation Key(s) field, enter the name of activation key previously created.
        10. Click the Generate command.
        11. Copy the generated curl command.
        12. Configure host with the CA certificate:
            # yum localinstall -y
            http://satellite.example.com/pub/katello-ca-consumer-latest.noarch.rpm
        13. On the host, enter the curl command as root.


    :expectedresults: Client appears in Insights Inventory

    :CaseAutomation: NotAutomated
    """
    pass


def test_positive_unregister_client_from_insights(vm, autosession):
    """Verify unregistration via insights-client.

    :id: 70d1045b-7d9d-472e-8ce9-8a5b81c41a85

    :expectedresults: Client should disappear from Insights > Inventory.
    """
    vm.unregister_insights()
    table = autosession.insightsinventory.search(vm.hostname)
    assert table.row_count == 0


@pytest.mark.parametrize('nav_item', NAV_ITEMS, ids=lambda nav_item: nav_item[0])
def test_insights_navigation(autosession, nav_item):
    """Test navigation across Insights tabs

    :id: 1f5faa05-83c2-43b3-925a-78c77d30d1ef

    :parametrized: yes

    :expectedresults: All pages should be opened correctly without 500 error
    """
    entity_name, destination = nav_item
    entity = getattr(autosession, entity_name)
    view = entity.navigate_to(entity, destination)
    assert view.is_displayed


def test_negative_org_not_selected(autosession):
    """Verify that user attempting to access RHAI is directed to select an
    Organization if there is no organization selected

    :id: 6ddfdb29-eeb5-41a4-8851-ad19130b112c

    :expectedresults: 'Organization Selection Required' message must be displayed if the user
        tries to view Insights overview without selecting an org
    """
    autosession.organization.select(org_name=ANY_CONTEXT['org'])
    with pytest.raises(InsightsOrganizationPageError, match='Organization Selection Required'):
        autosession.insightsoverview.read()


@pytest.mark.stubbed
def test_positive_rule_disable_enable():
    """Tests Insights rule can be disabled and enabled

    :id: ca61b798-7502-43a0-9045-392b350fdded

    :Steps:

        0. Create a VM and register to insights within org having manifest

        1. Navigate to Insights -> Rules

        2. Disable the chosen rule (assert)

        3. Enable chosen rule (assert)

    :expectedresults: rule is disabled, rule is enabled

    :CaseAutomation: NotAutomated

    :CaseLevel: System
    """


def test_positive_playbook_run(vm_rhel8, autosession, test_name, ansible_fixable_vm):
    """Tests Planner playbook runs successfully

    :id: b4cce0dc-c98e-4e1a-9dac-cdee3be05227

    :Steps:

        0. Create a VM and register to insights within org having manifest

        1. Navigate to Insights -> Planner

        2. Create a plan

        3. Assign specific host to the plan

        4. Assign a rule with ansible support to the plan

        5. Run Playbook

        6. Check the result at the host


    :expectedresults: playbook run finished successfully

    :CaseAutomation: NotAutomated

    :CaseLevel: System
    """
    plan_name = f'{test_name}_{gen_string("alpha", 6)}'
    autosession.insightsplan.create(plan_name, ['/etc/dnf/dnf.conf'])
    result = autosession.insightsplan.run_playbook(plan_name)

    assert result['overview']['job_status'] == 'Success'
    assert result['overview']['job_status_progress'] == '100%'


def test_positive_playbook_customized_run(vm_rhel8, autosession, test_name, ansible_fixable_vm):
    """Tests Planner playbook customized run is successful

    :id: eee4556d-69b9-4e89-88b7-3cc34a3fe3b2

    :Steps:

        0. Create a VM and register to insights within org having manifest

        1. Navigate to Insights -> Planner

        2. Create a plan

        3. Assign specific host to the plan

        4. Assign a rule with ansible support to the plan

        5. Customize Playbook Run

        6. Run the customized job

        7. Check the result at the host


    :expectedresults: customized playbook run finished successfully

    :CaseAutomation: Automated

    :CaseLevel: System
    """
    customize_values = {'advanced_options.execution_order': 'Randomized'}
    plan_name = f'{test_name}_{gen_string("alpha", 6)}'
    autosession.insightsplan.create(plan_name, ['/etc/dnf/dnf.conf'])
    result = autosession.insightsplan.run_playbook(
        plan_name, customize=True, customize_values=customize_values
    )

    assert result['overview']['job_status'] == 'Success'
    assert result['overview']['job_status_progress'] == '100%'


def test_positive_playbook_download(vm_rhel8, autosession, test_name, ansible_fixable_vm):
    """Tests Planner playbook download is successful

    :id: 7e9ed852-3f23-4256-862c-1d05058e8a95

    :Steps:

        0. Create a VM and register to insights within org having manifest

        1. Navigate to Insights -> Planner

        2. Create a plan

        3. Assign specific host to the plan

        4. Assign a rule with ansible support to the plan

        5. Download Playbook

        6. Check the downloaded result

    :expectedresults: sane playbook downloaded

    :CaseAutomation: Automated

    :CaseLevel: System
    """
    plan_name = f'{test_name}_{gen_string("alpha", 6)}'
    autosession.insightsplan.create(plan_name, ['/etc/dnf/dnf.conf'])
    file_path = autosession.insightsplan.download_playbook(plan_name)

    with open(file_path) as yamlfile:
        yaml_content = yaml.load(yamlfile, Loader=yaml.SafeLoader)

    assert len(yaml_content) >= 2
    for rule in yaml_content:
        assert vm_rhel8.hostname in rule['hosts'].split(',')

    dnf_rule = next(rule for rule in yaml_content if '/etc/dnf/dnf.conf' in rule['name'])
    task_names = [task['name'] for task in dnf_rule['tasks']]
    assert 'Set best option in file /etc/dnf/dnf.conf' in task_names


def test_positive_plan_export_csv(vm_rhel8, autosession, test_name, ansible_fixable_vm):
    """Tests Insights plan is exported to csv successfully

    :id: 4bf67758-e07a-41de-974f-9eda753d28e1

    :Steps:

        0. Create a VM and register to insights within org having manifest

        1. Navigate to Insights -> Planner

        2. Create a plan

        3. Assign specific host to the plan

        4. Assign any rule to the plan

        5. Export CSV

        6. Check the exported plan CSV


    :expectedresults: plan exported to sane csv file

    :CaseAutomation: Automated

    :CaseLevel: System
    """
    expected_keys = {
        'Hostname',
        'Machine ID',
        'Description',
        'Category',
        'Severity',
        'Article',
        'Completed',
        'Scheduled start (UTC)',
        'Scheduled end (UTC)',
    }
    rule_description = (
        'The dnf installs lower versions of packages when the "best" option '
        'is not present in the /etc/dnf/dnf.conf'
    )
    plan_name = f'{test_name}_{gen_string("alpha", 6)}'
    autosession.insightsplan.create(plan_name, ['/etc/dnf/dnf.conf'])
    file_path = autosession.insightsplan.export_csv(plan_name)

    with open(file_path) as csvfile:
        reader = csv.DictReader(csvfile)
        csv_content = [line for line in reader]

    assert len(csv_content) >= 1
    assert set(csv_content[0].keys()) == expected_keys
    hostnames = [entry['Hostname'] for entry in csv_content]
    assert vm_rhel8.hostname in hostnames
    vm_row = hostnames.index(vm_rhel8.hostname)
    assert csv_content[vm_row]['Description'] == rule_description


@pytest.mark.stubbed
def test_positive_plan_edit_remove_system():
    """Tests Insights plan can be edited by removing a system from it

    :id: d4ea837e-48b0-4482-a1a7-0507346519d7

    :Steps:

        0. Create a VM and register to insights within org having manifest

        1. Navigate to Insights -> Planner

        2. Create a plan

        3. Assign specific host to the plan

        4. Assign any rule to the plan

        5. Edit the plan and remove assigned system

        6. Check the plan become empty


    :expectedresults: plan becomes empty

    :CaseAutomation: NotAutomated

    :CaseLevel: System
    """
    pass


@pytest.mark.stubbed
def test_positive_plan_edit_remove_rule():
    """Tests Insights plan can be edited by removing a rule from it

    :id: dd05f149-b6ca-4845-8824-87e21d7b46e1

    :Steps:

        0. Create a VM and register to insights within org having manifest

        1. Navigate to Insights -> Planner

        2. Create a plan

        3. Assign specific host to the plan

        4. Assign any rule to the plan

        5. Edit the plan and remove assigned rule

        6. Check the plan do not contain the rule


    :expectedresults: rule is not present in the plan

    :CaseAutomation: NotAutomated

    :CaseLevel: System
    """
    pass


@pytest.mark.stubbed
def test_positive_inventory_export_csv():
    """Tests Insights inventory can be exported to csv

    :id: df4085f4-b058-4c2f-974f-89bc90d83c9c

    :Steps:

        0. Create a VM and register to insights within org having manifest

        1. Navigate to Insights -> Inventory

        2. Export CSV


    :expectedresults: inventory is exported in sane csv file

    :CaseAutomation: NotAutomated

    :CaseLevel: System
    """
    pass


@pytest.mark.stubbed
def test_positive_inventory_create_new_plan():
    """Tests Insights plan can be created using chosen inventory

    :id: 5af59eb0-b5d3-4ddb-9c34-f5f0d79353cc

    :Steps:

        0. Create a VM and register to insights within org having manifest

        1. Navigate to Insights -> Inventory

        2. In Actions select Create new Plan/Playbook for a system

    :expectedresults: new plan is created and involves the chosen system

    :CaseAutomation: NotAutomated

    :CaseLevel: System
    """
    pass


@pytest.mark.stubbed
def test_positive_inventory_add_to_existing_plan():
    """Tests Insights inventory system can be added to the existing plan

    :id: 1a1923d0-22d3-4ecc-b9cb-ec8ebc2d9155

    :Steps:

        0. Create a VM and register to insights within org having manifest

        1. Navigate to Insights -> Inventory

        2. In Actions select Create new Plan/Playbook for a system1

        3. In Actions select Add to existing Plan/Playbook for a system2

        4. Check that original plan contains also system2


    :expectedresults: existing plan gets extended of new system

    :CaseAutomation: NotAutomated

    :CaseLevel: System
    """
    pass


@pytest.mark.stubbed
def test_positive_inventory_group_systems():
    """Tests Insights inventory systems can be grouped

    :id: d6a2496f-b038-4d2b-80f9-95ef00225eb7

    :Steps:

        0. Create a VM and register to insights within org having manifest

        1. Navigate to Insights -> Inventory

        2. In Actions select Group systems and create new system group

        3. Check that selected system(s) are grouped in system group


    :expectedresults: systems are groupped in new Insights system group

    :CaseAutomation: NotAutomated

    :CaseLevel: System
    """
    pass


def test_numeric_group(vm, autosession):
    """Check the rule appears when provoked and disappears on Satellite once applied.

    :id: 4562e0f9-fff1-4cc7-b7e7-e4779662b3e1

    :expectedresults: rule no more appears on Rules page on portal
    """
    rule_title = 'Unexpected behavior: Numeric user or group names'
    values = autosession.insightsinventory.read(vm.hostname, 'rules')
    # assert that the user and group numeric rule is not present
    assert not [rule for rule in values['rules'] if rule_title in rule['title']]
    # as groupadd with numeric value should fail, add a valid group and replace it with a numeric
    # one in the group file.
    vm.execute('groupadd test_group')
    vm.execute("sed -i 's/test_group/123456/' /etc/group")
    vm.execute('insights-client')
    values = autosession.insightsinventory.read(vm.hostname, 'rules')
    # assert that the user and group numeric rule is present
    assert [rule for rule in values['rules'] if rule_title in rule['title']]
    vm.execute('groupdel 123456')
    vm.execute('insights-client')
    values = autosession.insightsinventory.read(vm.hostname, 'rules')
    # assert that the user and group numeric rule is not present again
    assert not [rule for rule in values['rules'] if rule_title in rule['title']]
