"""Test class for Virtwho Configure API

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
def test_positive_deploy_configure_script():
    """ Verify "POST /foreman_virt_who_configure/api/v2/configs"

    :id: b469822f-8b1f-437b-8193-6723ad3648dd

    :steps:
        1. Register the guest to satllite by CLI
        1. Create config by API
        2. Check the config by API
        3. Deploy the config by API
        4. Attach physical vdc to hypervisor, check the virtual
           vdc is generated and attachable in guest by API
        5. Delete config by API

    :expectedresults:
        1. Config can be created and deployed
        2. No error msg in /var/log/rhsm/rhsm.log
        3. Report is sent to satellite
        4. Virtual sku can be generated and attached
        5. Config can be deleted

    :CaseAutomation: notautomated
    """
