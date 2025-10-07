"""UI tests for Image Mode Hosts

:Requirement: ImageMode

:CaseAutomation: Automated

:CaseComponent: ImageMode

:Team: Artemis

:CaseImportance: High
"""

import json

from robottelo.constants import (
    DEFAULT_LOC,
    DUMMY_BOOTC_FACTS,
)


def test_bootc_booted_container_images(
    target_sat, dummy_bootc_host, function_ak_with_cv, function_org
):
    """Create a bootc host with a dummy facts file, and read its information via the Booted Container Images UI

    :id: c15f02a2-05e0-447a-bbcc-aace08d40d1a

    :expectedresults: Booted Container Images contains the correct information for a given booted image

    :Verifies:SAT-27163
    """
    bootc_dummy_info = json.loads(DUMMY_BOOTC_FACTS)
    assert (
        dummy_bootc_host.register(function_org, None, function_ak_with_cv.name, target_sat).status
        == 0
    )
    assert dummy_bootc_host.subscribed

    with target_sat.ui_session() as session:
        session.organization.select(function_org.name)
        booted_container_image_info = session.bootc.read(bootc_dummy_info['bootc.booted.image'])
        assert (
            booted_container_image_info[0]['Image name'] == bootc_dummy_info['bootc.booted.image']
        )
        assert booted_container_image_info[0]['Image digests'] == '1'
        assert booted_container_image_info[0]['Hosts'] == '1'
        assert (
            booted_container_image_info[1]['Image digest']
            == bootc_dummy_info['bootc.booted.digest']
        )
        assert booted_container_image_info[1]['Hosts'] == '1'


def test_bootc_host_details(target_sat, bootc_host, function_ak_with_cv, function_org):
    """Create a bootc host, and read it's information via the Host Details UI

    :id: 842356e9-8798-421d-aca6-0a1774c3f22b

    :expectedresults: Host Details UI contains the proper information for a bootc host

    :Verifies:SAT-27171
    """
    bootc_dummy_info = json.loads(DUMMY_BOOTC_FACTS)
    assert bootc_host.register(function_org, None, function_ak_with_cv.name, target_sat).status == 0
    assert bootc_host.subscribed

    with target_sat.ui_session() as session:
        session.organization.select(function_org.name)
        values = session.host_new.get_details(bootc_host.hostname, widget_names='details.bootc')
        assert (
            values['details']['bootc']['details']['running_image']
            == bootc_dummy_info['bootc.booted.image']
        )
        assert (
            values['details']['bootc']['details']['running_image_digest']
            == bootc_dummy_info['bootc.booted.digest']
        )
        assert (
            values['details']['bootc']['details']['rollback_image']
            == bootc_dummy_info['bootc.rollback.image']
        )
        assert (
            values['details']['bootc']['details']['rollback_image_digest']
            == bootc_dummy_info['bootc.rollback.digest']
        )


def test_bootc_rex_job(target_sat, bootc_host, function_ak_with_cv, function_org):
    """Run all bootc rex job (switch, upgrade, rollback, status) through Host Details UI

    :id: ef92a5f7-8cc7-4849-822c-90ea68b10554

    :expectedresults: Host Details UI links to the proper template, which runs successfully for all templates

    :Verifies:SAT-27154, SAT-27158
    """
    BOOTC_SWITCH_TARGET = "images.paas.redhat.com/bootc/rhel-bootc:latest-10.0"
    BOOTC_BASE_IMAGE = "localhost/tpl-bootc-rhel-10.0:latest"
    assert bootc_host.register(function_org, None, function_ak_with_cv.name, target_sat).status == 0
    assert bootc_host.subscribed

    with target_sat.ui_session() as session:
        session.organization.select(function_org.name)
        # bootc status
        session.host_new.run_bootc_job(bootc_host.hostname, 'status')
        task_result = target_sat.wait_for_tasks(
            search_query=(f'Remote action: Run Bootc status on {bootc_host.hostname}'),
            search_rate=2,
            max_tries=30,
        )
        task_status = target_sat.api.ForemanTask(id=task_result[0].id).poll()
        assert task_status['result'] == 'success'
        assert f'image: {BOOTC_BASE_IMAGE}' in task_status['humanized']['output']
        assert 'Successfully updated the system facts.' in task_status['humanized']['output']
        # bootc switch
        session.host_new.run_bootc_job(
            bootc_host.hostname, 'switch', job_options=BOOTC_SWITCH_TARGET
        )
        task_result = target_sat.wait_for_tasks(
            search_query=(f'Remote action: Run Bootc switch on {bootc_host.hostname}'),
            search_rate=2,
            max_tries=30,
        )
        task_status = target_sat.api.ForemanTask(id=task_result[0].id).poll()
        assert task_status['result'] == 'success'
        assert 'Successfully updated the system facts.' in task_status['humanized']['output']
        assert f'Queued for next boot: {BOOTC_SWITCH_TARGET}' in task_status['humanized']['output']
        # bootc upgrade
        session.host_new.run_bootc_job(bootc_host.hostname, 'upgrade')
        task_result = target_sat.wait_for_tasks(
            search_query=(f'Remote action: Run Bootc upgrade on {bootc_host.hostname}'),
            search_rate=2,
            max_tries=30,
        )
        task_status = target_sat.api.ForemanTask(id=task_result[0].id).poll()
        assert task_status['result'] == 'success'
        assert 'Successfully updated the system facts.' in task_status['humanized']['output']
        assert f'No changes in {BOOTC_SWITCH_TARGET}' in task_status['humanized']['output']
        # reboot the host, to ensure there is a rollback image
        bootc_host.execute('reboot')
        bootc_host.wait_for_connection()
        # bootc rollback
        session.host_new.run_bootc_job(bootc_host.hostname, 'rollback')
        task_result = target_sat.wait_for_tasks(
            search_query=(f'Remote action: Run Bootc rollback on {bootc_host.hostname}'),
            search_rate=2,
            max_tries=30,
        )
        task_status = target_sat.api.ForemanTask(id=task_result[0].id).poll()
        assert task_status['result'] == 'success'
        assert 'Next boot: rollback deployment' in task_status['humanized']['output']
        assert 'Successfully updated the system facts.' in task_status['humanized']['output']
        # Check that the display in host details matches the task output
        values = session.host_new.get_details(bootc_host.hostname, widget_names='details.bootc')
        assert values
        assert values['details']['bootc']['details']['running_image'] == BOOTC_SWITCH_TARGET
        assert values['details']['bootc']['details']['rollback_image'] == BOOTC_BASE_IMAGE


def test_bootc_transient_install_warning(target_sat, bootc_host, function_ak_with_cv, function_org):
    """Create a bootc host, and verify that all expected places warn you that package
    installs will be transient.

    :id: 10aea249-4e46-4e4f-a435-cff7e92afbdd

    :steps:
        1.Create and register a bootc host.
        2.Navigate to the All Hosts UI, and the Manage Packages and Manage Errata wizards.


    :expectedresults: In the 3 above cases, it is communicated to the user that package/errata actions will be transient.

    :Verifies: SAT-31251
    """
    assert bootc_host.register(function_org, None, function_ak_with_cv.name, target_sat).status == 0
    assert bootc_host.subscribed

    with target_sat.ui_session() as session:
        session.organization.select(function_org.name)
        session.location.select(loc_name=DEFAULT_LOC)
        # Check the banner on the Content tab of All Hosts
        values = session.host_new.get_details(
            bootc_host.hostname, widget_names='content.transient_install_alert'
        )
        assert (
            values["content"]["transient_install_alert"]
            == 'Any updates to image mode host(s) will be lost on the next reboot.'
        )
        # Check the banner on the Manage Packages and Manage Errata wizards
        values = session.all_hosts.get_package_and_errata_wizard_review_hosts_text()
        banner_string = "Note that package actions on any image mode hosts will be transient and lost on the next reboot."
        assert banner_string in values[0]
        assert banner_string in values[1]
