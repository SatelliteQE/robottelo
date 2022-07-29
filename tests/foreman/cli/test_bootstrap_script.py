"""Test for bootstrap script (bootstrap.py)

:Requirement: Bootstrap Script

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Bootstrap

:Assignee: sbible

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest


@pytest.mark.rhel_ver_list([7, 8])
@pytest.mark.tier1
def test_positive_register(
    module_org,
    module_location,
    module_lce,
    module_ak_cv_lce,
    module_published_cv,
    target_sat,
    rhel_contenthost,
):
    """System is registered

    :id: e34561fd-e0d6-4587-84eb-f86bd131aab1

    :Steps:

        1. Ensure system is not registered
        2. Register a system
        3. Ensure system is registered
        4. Register system once again


    :expectedresults: system is registered, host is created

    :CaseAutomation: Automated

    :CaseImportance: Critical

    :customerscenario: true

    :BZ: 2001476
    """
    if rhel_contenthost.os_version.major == 7:
        python_cmd = 'python'
    elif rhel_contenthost.os_version.major == 8:
        python_cmd = '/usr/libexec/platform-python'
    else:
        python_cmd = 'python3'
    hg = target_sat.api.HostGroup(location=[module_location], organization=[module_org]).create()
    # assure system is not registered
    result = rhel_contenthost.execute('subscription-manager identity')
    # result will be 1 if not registered
    assert result.status == 1
    assert rhel_contenthost.execute(
        f'curl -o /root/bootstrap.py "http://{target_sat.hostname}/pub/bootstrap.py" '
    )
    assert rhel_contenthost.execute(
        f'{python_cmd} /root/bootstrap.py -s {target_sat.hostname} -o {module_org.name}'
        f' -L {module_location.name} -a {module_ak_cv_lce.name} --hostgroup={hg.name}'
        ' --skip puppet --skip foreman'
    )
    # assure system is registered
    result = rhel_contenthost.execute('subscription-manager identity')
    # result will be 0 if registered
    assert result.status == 0
    # register system once again
    assert rhel_contenthost.execute(
        f'{python_cmd} /root/bootstrap.py -s "{target_sat.hostname}" -o {module_org.name} '
        f'-L {module_location.name} -a {module_ak_cv_lce.name} --hostgroup={hg.name}'
        '--skip puppet --skip foreman '
    )
    # assure system is registered
    result = rhel_contenthost.execute('subscription-manager identity')
    # result will be 0 if registered
    assert result.status == 0
