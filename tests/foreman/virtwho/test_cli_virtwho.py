"""Test class for Virtwho Configure CLI

:Requirement: Virt-whoConfigurePlugin

:CaseAutomation: notautomated

:CaseLevel: Acceptance

:CaseComponent: Virt-whoConfigurePlugin

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from robottelo.decorators import tier1


@tier1
def test_positive_deploy_configure_by_id():
    """ Verify " hammer virt-who-config deploy"

    :id: d5a0e807-8e61-4f9e-9177-c4d07b86500f

    :steps:
        1. Register the guest to satellite
        2. Create config by hammer virt-who-config create
        3. Check the config id by hammer virt-who-config list
        4. Deploy the config by hammer virt-who-config deploy
        5. Attach physical vdc to hypervisor, check the virtual
           vdc is generated and attachable in guest
        6. Delete config by hammer virt-who-config delete

    :expectedresults:
        1. Config can be created and deployed
        2. No error msg in /var/log/rhsm/rhsm.log
        3. Report is sent to satellite
        4. Virtual sku can be generated and attached
        5. Config can be deleted

    :CaseAutomation: notautomated
    """


@tier1
def test_positive_deploy_configure_by_script():
    """ Verify " hammer virt-who-config fetch"

    :id: 86ad13ec-2c52-4737-b54b-4bab03161923

    :steps:
        1. Register the guest to satellite
        2. Create config by hammer virt-who-config create
        3. Check the config id by hammer virt-who-config list
        4. Download the config script by hammer virt-who-config fetch
        5. Run the script
        6. Attach physical vdc to hypervisor, check the virtual
           vdc is generated and attachable in guest
        7. Delete config by hammer virt-who-config delete

    :expectedresults:
        1. Config can be created and downloaded
        2. No error msg in /var/log/rhsm/rhsm.log
        3. Report is sent to satellite
        4. Virtual sku can be generated and attached
        5. Config can be deleted

    :CaseAutomation: notautomated
    """


@tier1
def test_positive_update_configure_interval():
    """ Verify " hammer virt-who-config update"

    :id: 562c5054-49ba-4c89-9db7-73659c7ac9ef

    :steps:
        1. Create config by hammer virt-who-config create
        2. Check the config id by hammer virt-who-config list
        3. Deploy the config by hammer virt-who-config deploy
        4. Update VIRTWHO_INTERVAL to differernt value
        by hammer virt-who-config update
        5. Deploy the config again by hammer virt-who-config deploy

    :expectedresults:
        1. Config can be created and deployed
        2. Config VIRTWHO_INTERVAL be updated in /etc/sysconfig/virt-who

    :CaseAutomation: notautomated
    """
